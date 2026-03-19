# app/discord/views/reviews/review_form_view.py
"""
View для заполнения игрового отзыва (эфемеральное сообщение).

Открывается из ReviewInviteView при нажатии «Оставить отзыв».
Содержит все кнопки редактирования: оценка, комментарий, сцены, НИП,
лучший игрок, обновить, отменить, отправить.
"""
from __future__ import annotations

import logging
from uuid import UUID

import disnake
from disnake.ui import Button, button

from app.discord.dependencies import game_review_service_ctx
from app.discord.embeds.reviews.build_review_form_embed import build_review_form_embed
from app.discord.modals.reviews.review_comment_modal import ReviewCommentModal
from app.discord.modals.reviews.review_npc_modal import ReviewNpcModal
from app.discord.modals.reviews.review_scene_modal import ReviewSceneModal
from app.discord.views.base_view import BaseView
from app.discord.views.reviews.review_scene_type_view import ReviewSceneTypeView
from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.dto.game_review_dtos import UpdateGameReviewDTO, SendGameReviewDTO

logger = logging.getLogger(__name__)

# Таймаут формы: 30 минут
_FORM_TIMEOUT = 30 * 60

_RATING_EMOJI: dict[ReviewRatingEnum, str] = {
    ReviewRatingEnum.TERRIBLE:  "😡",
    ReviewRatingEnum.BAD:       "😕",
    ReviewRatingEnum.NEUTRAL:   "😐",
    ReviewRatingEnum.GOOD:      "🙂",
    ReviewRatingEnum.EXCELLENT: "🤩",
}


class ReviewFormView(BaseView):
    """
    Основная эфемеральная вьюшка заполнения отзыва.

    Параметры:
        review_id      — UUID отзыва в БД
        user_id        — UUID пользователя
        attending_players  — список (UUID, login) присутствовавших игроков (для выбора лучшего),
                           собирается в ReviewInviteView за один проход
    """

    def __init__(
        self,
        review_id: UUID,
        user_id: UUID,
        attending_players: list[tuple[UUID, str]] | None = None,
    ) -> None:
        super().__init__(timeout=_FORM_TIMEOUT)
        self._review_id = review_id
        self._user_id = user_id
        # list of (user_id, login) — готовые данные из ReviewInviteView
        self._attending_players: list[tuple[UUID, str]] = attending_players or []

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _refresh(self, inter: disnake.MessageInteraction) -> None:
        """Перерисовывает embed с актуальным состоянием отзыва."""
        async with game_review_service_ctx() as svc:
            review = await svc.get_by_id(self._review_id)
        await inter.edit_original_response(
            embed=build_review_form_embed(review), view=self
        )

    async def _update_field(
        self, inter: disnake.MessageInteraction, dto: UpdateGameReviewDTO
    ) -> None:
        """Сохраняет обновление и перерисовывает embed."""
        async with game_review_service_ctx() as svc:
            await svc.update(self._review_id, dto, self._user_id)
        async with game_review_service_ctx() as svc:
            review = await svc.get_by_id(self._review_id)
        try:
            await inter.edit_original_response(embed=build_review_form_embed(review), view=self)
        except disnake.HTTPException:
            pass

    # ── Рейтинг ───────────────────────────────────────────────────────────────

    @button(emoji="😡", style=disnake.ButtonStyle.secondary, custom_id="review_form:terrible", row=0)
    async def btn_terrible(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._update_field(inter, UpdateGameReviewDTO(rating=ReviewRatingEnum.TERRIBLE))

    @button(emoji="😕", style=disnake.ButtonStyle.secondary, custom_id="review_form:bad", row=0)
    async def btn_bad(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._update_field(inter, UpdateGameReviewDTO(rating=ReviewRatingEnum.BAD))

    @button(emoji="😐", style=disnake.ButtonStyle.secondary, custom_id="review_form:neutral", row=0)
    async def btn_neutral(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._update_field(inter, UpdateGameReviewDTO(rating=ReviewRatingEnum.NEUTRAL))

    @button(emoji="🙂", style=disnake.ButtonStyle.secondary, custom_id="review_form:good", row=0)
    async def btn_good(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._update_field(inter, UpdateGameReviewDTO(rating=ReviewRatingEnum.GOOD))

    @button(emoji="🤩", style=disnake.ButtonStyle.secondary, custom_id="review_form:excellent", row=0)
    async def btn_excellent(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._update_field(inter, UpdateGameReviewDTO(rating=ReviewRatingEnum.EXCELLENT))

    # ── Комментарий ───────────────────────────────────────────────────────────

    @button(label="💬 Комментарий", style=disnake.ButtonStyle.primary, custom_id="review_form:comment", row=1)
    async def btn_comment(self, _: Button, inter: disnake.MessageInteraction) -> None:
        async with game_review_service_ctx() as svc:
            review = await svc.get_by_id(self._review_id)

        async def on_comment(cb_inter: disnake.ModalInteraction, text: str) -> None:
            await self._update_field(cb_inter, UpdateGameReviewDTO(comment=text))
            await cb_inter.followup.send("✅ Комментарий сохранён.", ephemeral=True)

        modal = ReviewCommentModal(
            current_comment=review.comment or "",
            callback=on_comment,
        )
        await inter.response.send_modal(modal)

    # ── Сцены ─────────────────────────────────────────────────────────────────

    @button(label="🎬 Лучшие сцены", style=disnake.ButtonStyle.primary, custom_id="review_form:scenes", row=1)
    async def btn_scenes(self, _: Button, inter: disnake.MessageInteraction) -> None:
        """Шаг 1: пользователь вводит название сцены в модалке."""

        async def on_scene_name(modal_inter: disnake.ModalInteraction, scene_name: str) -> None:
            """Шаг 2: выбираем тип сцены через select view."""
            async def on_scene_type(
                type_inter: disnake.MessageInteraction,
                _scene_name: str,
                scene_type: str,
            ) -> None:
                async with game_review_service_ctx() as svc:
                    review = await svc.get_by_id(self._review_id)
                current_scenes: dict = dict(review.best_scenes or {})
                current_scenes[_scene_name] = scene_type
                await self._update_field(
                    type_inter,
                    UpdateGameReviewDTO(best_scenes=current_scenes),
                )
                await type_inter.followup.send(
                    f"✅ Сцена «{_scene_name}» добавлена.", ephemeral=True
                )

            scene_type_view = ReviewSceneTypeView(
                scene_name=scene_name,
                callback=on_scene_type,
            )
            await modal_inter.followup.send(
                "Выберите тип сцены:", view=scene_type_view, ephemeral=True
            )

        modal = ReviewSceneModal(callback=on_scene_name)
        await inter.response.send_modal(modal)

    # ── НИП ───────────────────────────────────────────────────────────────────

    @button(label="🧙 НИП", style=disnake.ButtonStyle.primary, custom_id="review_form:npc", row=1)
    async def btn_npc(self, _: Button, inter: disnake.MessageInteraction) -> None:
        async with game_review_service_ctx() as svc:
            review = await svc.get_by_id(self._review_id)

        async def on_npc(cb_inter: disnake.ModalInteraction, names: list[str]) -> None:
            await self._update_field(cb_inter, UpdateGameReviewDTO(best_npc=names))
            await cb_inter.followup.send("✅ НИП сохранены.", ephemeral=True)

        modal = ReviewNpcModal(
            current_npc=review.best_npc or [],
            callback=on_npc,
        )
        await inter.response.send_modal(modal)

    # ── Лучший игрок ──────────────────────────────────────────────────────────

    @button(label="🏆 Игрок сессии", style=disnake.ButtonStyle.primary, custom_id="review_form:best_player", row=2)
    async def btn_best_player(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        if not self._attending_players:
            await inter.followup.send(
                "ℹ️ Список присутствующих игроков недоступен.", ephemeral=True
            )
            return

        from app.discord.views.select_view import SelectView

        class _PlayerItem:
            def __init__(self, uid: UUID, display: str):
                self.id = uid
                self.name = display

        # Данные уже готовы — (uuid, login) собраны в ReviewInviteView.
        # Фильтруем только себя: голосовать за себя нельзя.
        items = [
            _PlayerItem(uid, login)
            for uid, login in self._attending_players
            if uid != self._user_id
        ]

        if not items:
            await inter.followup.send(
                "ℹ️ Нет других игроков для выбора.", ephemeral=True
            )
            return

        async def on_player_selected(cb_inter: disnake.MessageInteraction, player_id: str) -> None:
            await self._update_field(
                cb_inter,
                UpdateGameReviewDTO(best_player_id=UUID(player_id)),
            )
            await cb_inter.followup.send("✅ Лучший игрок выбран.", ephemeral=True)

        view = SelectView(
            items=items,
            display_field="name",
            title="Игрок сессии",
            callback=on_player_selected,
            skippable=True,
        )
        await inter.followup.send("Выберите лучшего игрока:", view=view, ephemeral=True)

    # ── Обновить ──────────────────────────────────────────────────────────────

    @button(label="🔄 Обновить", style=disnake.ButtonStyle.secondary, custom_id="review_form:refresh", row=2)
    async def btn_refresh(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._refresh(inter)

    # ── Отменить ──────────────────────────────────────────────────────────────

    @button(label="❌ Отменить", style=disnake.ButtonStyle.danger, custom_id="review_form:cancel", row=3)
    async def btn_cancel(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        async with game_review_service_ctx() as svc:
            await svc.cancel(self._review_id, self._user_id)
        self.stop()
        await inter.edit_original_response(
            embed=disnake.Embed(
                description="🕊️ В другой раз! Отзыв отменён.",
                color=disnake.Color.greyple(),
            ),
            view=None,
        )

    # ── Отправить анонимно ────────────────────────────────────────────────────

    @button(label="🎭 Отправить анонимно", style=disnake.ButtonStyle.success, custom_id="review_form:send_anon", row=3)
    async def btn_send_anon(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._do_send(inter, ReviewAnonymityEnum.PRIVATE)

    # ── Отправить публично ────────────────────────────────────────────────────

    @button(label="✅ Отправить публично", style=disnake.ButtonStyle.success, custom_id="review_form:send_public", row=3)
    async def btn_send_public(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await self._do_send(inter, ReviewAnonymityEnum.PUBLIC)

    # ── send logic ────────────────────────────────────────────────────────────

    async def _do_send(
        self,
        inter: disnake.MessageInteraction,
        anonymity: ReviewAnonymityEnum,
    ) -> None:
        async with game_review_service_ctx() as svc:
            review = await svc.get_by_id(self._review_id)

        # Проверяем обязательные поля до вызова сервиса
        missing: list[str] = []
        if not review.rating:
            missing.append("оценку (😡/😕/😐/🙂/🤩)")
        if not review.comment or not review.comment.strip():
            missing.append("комментарий (💬)")

        if missing:
            await inter.followup.send(
                f"⚠️ Перед отправкой укажите: {', '.join(missing)}.",
                ephemeral=True,
            )
            return

        async with game_review_service_ctx() as svc:
            await svc.send(
                self._review_id,
                SendGameReviewDTO(anonymity=anonymity),
                self._user_id,
            )

        self.stop()
        label = "анонимно" if anonymity == ReviewAnonymityEnum.PRIVATE else "публично"
        await inter.edit_original_response(
            embed=disnake.Embed(
                description=f"✅ Отзыв отправлен **{label}**! Спасибо за участие 🎲",
                color=disnake.Color.green(),
            ),
            view=None,
        )

    # ── Таймаут ───────────────────────────────────────────────────────────────

    async def on_timeout(self) -> None:
        """При таймауте — отменяем отзыв если он ещё не отправлен."""
        logger.info("[ReviewFormView] Timeout for review %s", self._review_id)
        try:
            async with game_review_service_ctx() as svc:
                review = await svc.get_by_id(self._review_id)
                if review.status.value == "created":
                    await svc.cancel(self._review_id, self._user_id)
        except Exception as e:
            logger.warning("[ReviewFormView] Could not auto-cancel review %s: %s", self._review_id, e)