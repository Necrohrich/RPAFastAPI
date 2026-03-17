# app/discord/views/attendance_view.py
"""
View для пошагового выбора присутствующих игроков перед стартом сессии.

Показывает принятых игроков по одному: GM отмечает ✅ Присутствует / ❌ Отсутствует.
По таймауту — все оставшиеся считаются присутствующими.

Жизненный цикл:
    1. Cog создаёт view и отправляет сообщение в канал.
    2. attendance_message_id сохраняется в discord_state сразу после отправки.
    3. Cog вызывает view.wait() — ожидает завершения или таймаута.
    4. Cog читает view.attending_ids и запускает сессию.
    5. При отмене/инвалидации — cog вызывает view.force_stop().
"""
from __future__ import annotations

import logging

import disnake
from disnake.ui import button, Button

from app.discord.embeds.build_attendance_embed import (
    build_attendance_embed,
    build_attendance_finished_embed,
    build_attendance_canceled_embed,
)
from app.discord.views.base_view import BaseView
from app.domain.entities import Game
from app.dto import GameSessionResponseDTO

logger = logging.getLogger(__name__)

ATTENDANCE_TIMEOUT = 30 * 60  # секунд


class AttendanceView(BaseView):
    """
    View для пошагового выбора присутствующих игроков.

    Параметры:
        session         — DTO текущей сессии
        game            — доменный объект игры
        player_entries  — список (discord_id, display_name) принятых игроков
        gm_discord_id   — Discord ID мастера (только он может нажимать кнопки)

    После завершения view.wait():
        attending_ids   — список discord_id присутствующих игроков (без GM)
    """

    def __init__(
        self,
        session: GameSessionResponseDTO,
        game: Game,
        player_entries: list[tuple[int, str]],
        gm_discord_id: int,
    ) -> None:
        super().__init__(timeout=ATTENDANCE_TIMEOUT)

        self.session = session
        self.game = game
        self.player_entries = player_entries
        self.gm_discord_id = gm_discord_id

        self.attending_ids: list[int] = []
        self._current_index: int = 0
        self._message: disnake.Message | None = None

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def set_message(self, message: disnake.Message) -> None:
        """Сохраняет ссылку на сообщение для редактирования при смене игрока."""
        self._message = message

    def current_embed(self) -> disnake.Embed:
        """Возвращает embed для текущего игрока."""
        discord_id, display_name = self.player_entries[self._current_index]
        return build_attendance_embed(
            self.session,
            self.game,
            display_name,
            self._current_index,
            len(self.player_entries),
        )

    async def force_stop(self) -> None:
        """
        Принудительно завершает View при отмене или инвалидации сессии.
        Редактирует сообщение и останавливает view.wait().
        """
        self.stop()
        if self._message:
            try:
                await self._message.edit(embed=build_attendance_canceled_embed(), view=None)
            except disnake.HTTPException:
                pass

    # ── Проверка автора ───────────────────────────────────────────────────────

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.gm_discord_id:
            await inter.response.send_message(
                "❌ Только мастер игры может отмечать присутствие.", ephemeral=True
            )
            return False
        return True

    # ── Кнопки ───────────────────────────────────────────────────────────────

    @button(label="✅ Присутствует", style=disnake.ButtonStyle.success, custom_id="attendance:present")
    async def present_button(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        discord_id, _ = self.player_entries[self._current_index]
        self.attending_ids.append(discord_id)
        await self._advance()

    @button(label="❌ Отсутствует", style=disnake.ButtonStyle.danger, custom_id="attendance:absent")
    async def absent_button(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        await self._advance()

    # ── Внутренняя логика ─────────────────────────────────────────────────────

    async def _advance(self) -> None:
        """Переходит к следующему игроку или завершает View."""
        self._current_index += 1

        if self._current_index >= len(self.player_entries):
            self.stop()
            if self._message:
                try:
                    await self._message.edit(
                        embed=build_attendance_finished_embed(
                            len(self.attending_ids),
                            len(self.player_entries),
                        ),
                        view=None,
                    )
                except disnake.HTTPException:
                    pass
            return

        if self._message:
            try:
                await self._message.edit(embed=self.current_embed(), view=self)
            except disnake.HTTPException:
                pass

    # ── Таймаут ──────────────────────────────────────────────────────────────

    async def on_timeout(self) -> None:
        """По таймауту все оставшиеся игроки считаются присутствующими."""
        remaining = self.player_entries[self._current_index:]
        logger.info(
            "[AttendanceView] Timeout for session %s — marking %d remaining as present",
            self.session.id, len(remaining),
        )
        for discord_id, _ in remaining:
            self.attending_ids.append(discord_id)

        if self._message:
            try:
                await self._message.edit(
                    embed=build_attendance_finished_embed(
                        len(self.attending_ids),
                        len(self.player_entries),
                    ),
                    view=None,
                )
            except disnake.HTTPException:
                pass