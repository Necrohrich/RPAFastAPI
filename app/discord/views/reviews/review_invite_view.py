# app/discord/views/reviews/review_invite_view.py
"""
Персистентная главная вьюшка приглашения к отзыву.

Footer формат: "session_id:{uuid}|game:{game_name}"

Таймаут вьюшки (60 минут) управляется здесь.
При истечении все CREATED-отзывы сессии переходят в CANCELED,
а само сообщение редактируется — кнопки убираются.

ReviewFormView работает без таймаута — всё управление временем здесь.
"""
from __future__ import annotations

import logging
from uuid import UUID

import disnake
from disnake.ui import Button, button

from app.discord.dependencies import game_review_service_ctx, user_service_ctx
from app.discord.embeds.reviews.build_review_form_embed import build_review_form_embed
from app.discord.views.base_view import BaseView
from app.discord.views.reviews.review_form_view import ReviewFormView
from app.dto.game_review_dtos import CreateGameReviewDTO, GameReviewResponseDTO
from app.exceptions.common_exceptions import NotFoundError
from app.exceptions.game_review_exceptions import (
    GameReviewAlreadyExistsException,
    GameReviewNotAllowedException,
)
from app.utils.mapper import Mapper

logger = logging.getLogger(__name__)

_INVITE_TIMEOUT = 5  # 60 минут


def _parse_footer(footer_text: str) -> tuple[UUID | None, str]:
    try:
        parts = dict(p.split(":", 1) for p in footer_text.split("|"))
        session_id = UUID(parts["session_id"])
        game_name = parts.get("game", "—")
        return session_id, game_name
    except Exception:
        return None, "—"


async def _get_session_id_and_attending(
    inter: disnake.MessageInteraction,
) -> tuple[UUID | None, list[int]]:
    session_id, _ = _parse_footer(
        inter.message.embeds[0].footer.text if inter.message.embeds else ""
    )
    if not session_id:
        return None, []

    attending: list[int] = []
    async with game_review_service_ctx() as svc:
        discord_state = await svc.session_repo.get_discord_state(session_id)
    if discord_state:
        attending = discord_state.get("attending_user_ids") or []

    return session_id, attending


async def _check_user_allowed(
    inter: disnake.MessageInteraction,
    attending_discord_ids: list[int],
) -> tuple[UUID | None, bool]:
    try:
        async with user_service_ctx() as u_svc:
            user_dto = await u_svc.get_user_by_discord(inter.author.id)
    except NotFoundError:
        await inter.followup.send("❌ Вы не зарегистрированы в системе.", ephemeral=True)
        return None, False

    if attending_discord_ids:
        user_discord_ids: set[int] = set()
        if user_dto.primary_discord_id:
            user_discord_ids.add(user_dto.primary_discord_id)
        if user_dto.secondary_discord_id:
            user_discord_ids.add(user_dto.secondary_discord_id)

        if user_discord_ids and not user_discord_ids.intersection(attending_discord_ids):
            await inter.followup.send(
                "❌ Вы не были отмечены как присутствующий на этой сессии.",
                ephemeral=True,
            )
            return None, False

    return user_dto.id, True


class ReviewInviteView(BaseView):
    """
    Главная вьюшка приглашения к отзыву.

    Таймаут: 60 минут. По истечении:
    - Все CREATED-отзывы сессии переходят в CANCELED.
    - Сообщение редактируется: кнопки убираются, embed заменяется финальным.

    set_message() должен быть вызван сразу после отправки сообщения,
    чтобы on_timeout мог его отредактировать.
    """

    def __init__(self, session_id: UUID | None = None) -> None:
        super().__init__(timeout=None)
        self._session_id = session_id
        self._message: disnake.Message | None = None

    @classmethod
    def with_timeout(cls, session_id: UUID) -> "ReviewInviteView":
        inst = cls(session_id=session_id)
        inst.timeout = _INVITE_TIMEOUT
        return inst

    def set_message(self, message: disnake.Message) -> None:
        """Сохраняет ссылку на сообщение для редактирования при таймауте."""
        self._message = message

    async def on_timeout(self) -> None:
        """
        При истечении таймаута:
        1. Отменяем все CREATED-отзывы сессии.
        2. Редактируем сообщение — убираем кнопки, показываем финальный embed.
        """
        if not self._session_id:
            return

        logger.info(
            "[ReviewInviteView] Timeout for session %s — canceling remaining CREATED reviews",
            self._session_id,
        )

        try:
            async with game_review_service_ctx() as svc:
                from app.domain.enums.review_status_enum import ReviewStatusEnum
                reviews = await svc.repo.get_list_by_session_id(
                    self._session_id,
                    statuses=[ReviewStatusEnum.CREATED],
                    include_deleted=False,
                )
                for review in reviews:
                    try:
                        await svc.cancel(review.id, review.user_id)
                    except Exception as exc:
                        logger.warning(
                            "[ReviewInviteView] Could not cancel review %s: %s", review.id, exc
                        )
        except Exception as exc:
            logger.error("[ReviewInviteView] on_timeout error while canceling: %s", exc)

        if self._message:
            try:
                await self._message.edit(
                    embed=disnake.Embed(
                        title="⏰ Время опроса истекло",
                        description="Окно для заполнения отзыва закрыто. Спасибо за участие!",
                        color=disnake.Color.greyple(),
                    ),
                    view=None,
                )
            except disnake.HTTPException as exc:
                logger.warning("[ReviewInviteView] Could not edit message on timeout: %s", exc)

    @button(
        label="✅ Оставить отзыв",
        style=disnake.ButtonStyle.success,
        custom_id="review_invite:yes",
        row=0,
    )
    async def btn_yes(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        session_id, attending = await _get_session_id_and_attending(inter)
        if not session_id:
            await inter.followup.send("❌ Не удалось определить сессию.", ephemeral=True)
            return

        user_id, allowed = await _check_user_allowed(inter, attending)
        if not allowed:
            return

        async with game_review_service_ctx() as svc:
            session = await svc.session_repo.get_by_id(session_id)
            if not session:
                await inter.followup.send("❌ Сессия не найдена.", ephemeral=True)
                return

        try:
            async with game_review_service_ctx() as svc:
                review = await svc.create(CreateGameReviewDTO(
                    game_id=session.game_id,
                    session_id=session_id,
                    user_id=user_id,
                ))
        except GameReviewAlreadyExistsException:
            async with game_review_service_ctx() as svc:
                existing = await svc.repo.get_by_session_id_and_user_id(
                    session_id, user_id, include_deleted=False
                )
            if not existing:
                await inter.followup.send("⚠️ Отзыв уже был отправлен или отменён.", ephemeral=True)
                return
            from app.domain.enums.review_status_enum import ReviewStatusEnum
            if existing.status != ReviewStatusEnum.CREATED:
                await inter.followup.send("⚠️ Отзыв уже был отправлен или отменён.", ephemeral=True)
                return
            review = Mapper.entity_to_dto(existing, GameReviewResponseDTO)
        except GameReviewNotAllowedException as exc:
            await inter.followup.send(f"❌ {exc}", ephemeral=True)
            return

        attending_players: list[tuple[UUID, str]] = []
        for did in attending:
            try:
                async with user_service_ctx() as u_svc:
                    u = await u_svc.get_user_by_discord(did)
                attending_players.append((u.id, u.login))
            except NotFoundError:
                pass

        form_view = ReviewFormView(
            review_id=review.id,
            user_id=user_id,
            attending_players=attending_players,
        )
        await inter.followup.send(
            embed=build_review_form_embed(review),
            view=form_view,
            ephemeral=True,
        )

    @button(
        label="❌ В другой раз",
        style=disnake.ButtonStyle.secondary,
        custom_id="review_invite:no",
        row=0,
    )
    async def btn_no(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        session_id, attending = await _get_session_id_and_attending(inter)
        if not session_id:
            await inter.followup.send("🕊️ Хорошо, в другой раз!", ephemeral=True)
            return

        user_id, allowed = await _check_user_allowed(inter, attending)
        if not allowed:
            return

        async with game_review_service_ctx() as svc:
            existing = await svc.repo.get_by_session_id_and_user_id(
                session_id, user_id, include_deleted=False
            )
            if existing:
                from app.domain.enums.review_status_enum import ReviewStatusEnum
                if existing.status == ReviewStatusEnum.CREATED:
                    await svc.cancel(existing.id, user_id)

        await inter.followup.send("🕊️ Хорошо, в другой раз!", ephemeral=True)