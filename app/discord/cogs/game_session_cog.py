# app/discord/cogs/game_session_cog.py
"""
Cog для обработки Discord Scheduled Events и управления игровыми сессиями.

Реализует этап 6.4: on_scheduled_event_create/update/start/end.
Этапы 6.5 (AttendanceView, session_roles helper) и 6.6 (slash-команды)
будут добавлены отдельно — этот файл уже подготовлен к их подключению.
"""
from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from app.discord.dependencies import game_session_service_ctx, guild_settings_service_ctx
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO
from app.exceptions import (
    GameSessionNotFoundException,
    GameSessionInvalidStatusTransitionException,
    GameNotFoundByEventTitleException,
)

logger = logging.getLogger(__name__)


# ── Вспомогательные функции отправки уведомлений ────────────────────────────

async def _notify_channel(
    bot: commands.InteractionBot,
    channel_id: int | None,
    role_id: int | None,
    text: str,
    color: disnake.Color = disnake.Color.blurple(),
) -> None:
    """Отправляет embed-уведомление в указанный канал с опциональным пингом роли."""
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.warning("Notification channel %s not found in cache", channel_id)
        return
    embed = disnake.Embed(description=text, color=color)
    content = f"<@&{role_id}>" if role_id else None
    try:
        await channel.send(content=content, embed=embed)
    except disnake.HTTPException as e:
        logger.error("Failed to send notification to channel %s: %s", channel_id, e)


async def _try_delete_attendance_message(
    bot: commands.InteractionBot,
    channel_id: int | None,
    message_id: int | None,
) -> None:
    """Удаляет сообщение с View выбора игроков, если оно ещё существует."""
    if not channel_id or not message_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    try:
        msg = await channel.fetch_message(message_id)
        await msg.delete()
    except (disnake.NotFound, disnake.HTTPException):
        pass


# ── Основной Cog ─────────────────────────────────────────────────────────────

class GameSessionCog(commands.Cog):
    """
    Обрабатывает Discord Scheduled Events и привязывает их к игровым сессиям.

    Жизненный цикл:
        CREATE  → автоматически создаёт GameSession (CREATED), если название
                  события содержит название игры (ILIKE поиск).
        UPDATE  → синхронизирует title/description/image_url; при отмене
                  Discord-события переводит сессию в CANCELED.
        START   → если сессия ещё не запущена — показывает AttendanceView
                  (TODO 6.5) и стартует сессию; если уже ACTIVE (запущена
                  через сайт) — сразу выдаёт роли и переименовывает ников.
        END     → завершает сессию, возвращает ники, удаляет временную роль.
    """

    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    # ── on_scheduled_event_create ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: disnake.GuildScheduledEvent) -> None:
        """
        Автоматически создаёт GameSession при создании Discord Scheduled Event.

        Алгоритм:
            1. Ищем игру, чьё название содержится в заголовке события (ILIKE).
            2. Если найдена — создаём сессию CREATED с привязкой discord_event_id.
            3. Если не найдена — логируем и молча пропускаем.
        """
        logger.info(
            "[on_scheduled_event_create] event_id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

        async with game_session_service_ctx() as service:
            # Ищем game_id по названию события
            game_id = await service.repo.find_game_id_by_event_title(event.name)

            if game_id is None:
                logger.info(
                    "[on_scheduled_event_create] No game matched for event %r — skipping",
                    event.name,
                )
                return

            # Проверяем, не привязана ли уже эта сессия (race condition guard)
            existing = await service.repo.get_by_discord_event_id(event.id)
            if existing:
                logger.info(
                    "[on_scheduled_event_create] Event %s already linked to session %s — skipping",
                    event.id, existing.id,
                )
                return

            dto = CreateGameSessionDTO(
                game_id=game_id,
                discord_event_id=event.id,
                title=event.name,
                description=event.description or "",
                image_url=str(event.image_url) if event.image_url else "",
            )
            session = await service.create(dto)
            logger.info(
                "[on_scheduled_event_create] Created session %s (#%s) for game %s",
                session.id, session.session_number, game_id,
            )

            # Уведомление в канал игры
            game = await service.game_repo.get_by_id(game_id)
            if game:
                await _notify_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"📅 Запланирована сессия #{session.session_number}: {session.title}",
                    color=disnake.Color.blue(),
                )

    # ── on_scheduled_event_update ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_update(
        self,
        before: disnake.GuildScheduledEvent,
        after: disnake.GuildScheduledEvent,
    ) -> None:
        """
        Синхронизирует данные сессии при изменении Discord события.

        Обновляет title / description / image_url при изменении.
        При отмене события (status → CANCELED) переводит сессию в CANCELED
        и удаляет сообщение AttendanceView если оно было отправлено.
        """
        logger.info(
            "[on_scheduled_event_update] event_id=%s status=%s→%s",
            after.id, before.status, after.status,
        )

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(after.id)
            if not session:
                return  # событие не привязано ни к одной сессии — игнорируем

            # ── Отмена Discord-события ───────────────────────────────────────
            if (
                after.status == disnake.GuildScheduledEventStatus.canceled
                and before.status != disnake.GuildScheduledEventStatus.canceled
            ):
                try:
                    result = await service.cancel(session.id)
                    logger.info(
                        "[on_scheduled_event_update] Session %s canceled via Discord event",
                        session.id,
                    )
                except GameSessionInvalidStatusTransitionException:
                    logger.warning(
                        "[on_scheduled_event_update] Cannot cancel session %s (status=%s)",
                        session.id, session.status,
                    )

                # Удаляем AttendanceView если он ещё висит
                discord_state = await service.repo.get_discord_state(session.id)
                game = await service.game_repo.get_by_id(session.game_id)
                if discord_state and discord_state.get("attendance_message_id"):
                    channel_id = game.discord_main_channel_id if game else None
                    await _try_delete_attendance_message(
                        self.bot,
                        channel_id=channel_id,
                        message_id=discord_state["attendance_message_id"],
                    )

                # Уведомление об отмене
                if game:
                    await _notify_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"❌ Сессия #{session.session_number} отменена",
                        color=disnake.Color.red(),
                    )
                return

            # ── Обновление полей сессии ──────────────────────────────────────
            changed: dict = {}
            if after.name != session.title:
                changed["title"] = after.name
            if (after.description or "") != (session.description or ""):
                changed["description"] = after.description or ""
            new_image = str(after.image_url) if after.image_url else ""
            if new_image != (session.image_url or ""):
                changed["image_url"] = new_image

            if changed:
                dto = UpdateGameSessionDTO(**changed)
                await service.update(session.id, dto)
                logger.info(
                    "[on_scheduled_event_update] Session %s updated fields: %s",
                    session.id, list(changed.keys()),
                )

    # ── on_scheduled_event_start ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_start(self, event: disnake.GuildScheduledEvent) -> None:
        """
        Обрабатывает старт Discord Scheduled Event.

        Два сценария:
            A) Сессия уже ACTIVE (запущена через сайт):
               - discord_state уже существует
               - Пропускаем AttendanceView
               - Выдаём роли и переименовываем ников по данным из discord_state
               - (TODO 6.5: session_roles helper)

            B) Сессия ещё CREATED:
               - Показываем AttendanceView в discord_main_channel_id
               - AttendanceView блокирует выполнение до завершения
               - После — вызываем service.start(attending_user_ids)
               - Выдаём роли и переименовываем ников
               - (TODO 6.5: AttendanceView + session_roles helper)
        """
        logger.info(
            "[on_scheduled_event_start] event_id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info(
                    "[on_scheduled_event_start] No session linked to event %s — skipping",
                    event.id,
                )
                return

            game = await service.game_repo.get_by_id(session.game_id)
            discord_state = await service.repo.get_discord_state(session.id)

            # ── Сценарий A: сессия уже ACTIVE (запущена через сайт) ─────────
            if discord_state is not None:
                logger.info(
                    "[on_scheduled_event_start] Session %s already active (started via site), "
                    "applying roles from existing discord_state",
                    session.id,
                )
                attending_user_ids = discord_state.get("attending_user_ids", [])

                # TODO 6.5 — вызов session_roles.assign_session_roles(guild, game, attending_user_ids, discord_state)
                logger.info(
                    "[on_scheduled_event_start] [STUB] Would assign roles to %d users",
                    len(attending_user_ids),
                )

                if game:
                    await _notify_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )
                return

            # ── Сценарий B: сессия не запущена, нужен AttendanceView ─────────
            channel_id = game.discord_main_channel_id if game else None
            channel = self.bot.get_channel(channel_id) if channel_id else None

            if not channel:
                logger.warning(
                    "[on_scheduled_event_start] discord_main_channel_id not configured "
                    "for game %s — starting session without attendance check",
                    session.game_id,
                )
                # Запускаем без выбора присутствующих — считаем всех присутствующими
                await service.start(session.id, attending_user_ids=[])
                logger.info(
                    "[on_scheduled_event_start] Session %s started (no channel — empty attendance)",
                    session.id,
                )
                return

            # TODO 6.5 — создать и отправить AttendanceView:
            #
            #   view = AttendanceView(session=session, game=game, timeout=ATTENDANCE_TIMEOUT)
            #   msg = await channel.send(embed=build_attendance_embed(session, game), view=view)
            #
            #   # Сохраняем attendance_message_id в discord_state (создаём временный)
            #   await service.repo.create_discord_state(
            #       session_id=session.id,
            #       attendance_message_id=msg.id,
            #   )
            #
            #   await view.wait()  # блокируем до завершения
            #   attending_user_ids = view.result  # список Discord ID
            #
            #   await service.start(session.id, attending_user_ids=attending_user_ids)
            #   # TODO 6.5 — assign_session_roles(guild, game, attending_user_ids, ...)

            # STUB: до реализации 6.5 стартуем с пустым attendance
            logger.info(
                "[on_scheduled_event_start] [STUB] AttendanceView not implemented yet — "
                "starting session %s with empty attendance",
                session.id,
            )
            try:
                await service.start(session.id, attending_user_ids=[])
            except GameSessionInvalidStatusTransitionException:
                logger.warning(
                    "[on_scheduled_event_start] Cannot start session %s (bad status=%s)",
                    session.id, session.status,
                )
                return

            if game:
                await _notify_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"🎲 Сессия #{session.session_number} началась!",
                    color=disnake.Color.green(),
                )

    # ── on_scheduled_event_end ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_end(self, event: disnake.GuildScheduledEvent) -> None:
        """
        Обрабатывает окончание Discord Scheduled Event.

        Алгоритм:
            1. Находим сессию по discord_event_id.
            2. Вызываем service.complete() — переводит в COMPLETED, удаляет discord_state.
            3. TODO 6.5 — restore_after_session: вернуть ники, удалить временную роль.
        """
        logger.info(
            "[on_scheduled_event_end] event_id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info(
                    "[on_scheduled_event_end] No session linked to event %s — skipping",
                    event.id,
                )
                return

            # Снимаем discord_state до завершения (нужен для restore)
            discord_state = await service.repo.get_discord_state(session.id)
            game = await service.game_repo.get_by_id(session.game_id)

            try:
                await service.complete(session.id)
                logger.info("[on_scheduled_event_end] Session %s completed", session.id)
            except GameSessionInvalidStatusTransitionException:
                logger.warning(
                    "[on_scheduled_event_end] Cannot complete session %s (status=%s)",
                    session.id, session.status,
                )
                return

            # TODO 6.5 — вызов restore_after_session(guild, discord_state):
            #   - вернуть оригинальные ники (из discord_state["original_nicknames"])
            #   - вернуть аватары участников
            #   - удалить временную роль по discord_state["temp_role_id"]
            if discord_state:
                temp_role_id = discord_state.get("temp_role_id")
                logger.info(
                    "[on_scheduled_event_end] [STUB] Would restore nicks and delete temp_role=%s",
                    temp_role_id,
                )

            # Уведомление о завершении
            if game:
                await _notify_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"✅ Сессия #{session.session_number} завершена",
                    color=disnake.Color.green(),
                )


# ── setup ─────────────────────────────────────────────────────────────────────

def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(GameSessionCog(bot))
    logger.info("GameSessionCog loaded")