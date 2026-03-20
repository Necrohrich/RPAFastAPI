# app/discord/views/reviews/review_invite_view.py
"""
Персистентная главная вьюшка приглашения к отзыву.

Footer формат: "session_id:{uuid}|game:{game_name}"

Таймаут вьюшки (60 минут) управляется здесь.
При истечении все CREATED-отзывы сессии переходят в CANCELED.

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

# 60 минут — общий дедлайн для всей системы отзывов сессии
_INVITE_TIMEOUT = 60 * 60


def _parse_footer(footer_text: str) -> tuple[UUID | None, str]:
    """Извлекает session_id и game_name из footer embed."""
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
    """Возвращает session_id и список attending discord_id из footer + discord_state."""
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
    """
    Проверяет, имеет ли пользователь право взаимодействовать с вьюшкой.

    Возвращает (user_id, allowed).

    Правила:
    - Пользователь должен быть зарегистрирован в системе.
    - Если attending_discord_ids непустой — discord_id пользователя должен
      быть в этом списке (т.е. он присутствовал на сессии).
    - Если attending пустой (сессия через сайт без AttendanceView) —
      проверка присутствия пропускается, достаточно быть игроком.
    """
    try:
        async with user_service_ctx() as u_svc:
            user_dto = await u_svc.get_user_by_discord(inter.author.id)
    except NotFoundError:
        await inter.followup.send(
            "❌ Вы не зарегистрированы в системе.", ephemeral=True
        )
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
    Главная персистентная вьюшка отзывов.

    Таймаут: 60 минут. По истечении все незакрытые CREATED-отзывы сессии
    переходят в CANCELED.

    ReviewFormView создаётся без таймаута — время жизни формы полностью
    определяется таймаутом этой вьюшки.
    """

    def __init__(self, session_id: UUID | None = None) -> None:
        # timeout=None → персистентная (для register_views); timeout задаётся
        # при отправке в канал через конкретный экземпляр.
        # Для register_views() нужен экземпляр без таймаута.
        super().__init__(timeout=None)
        self._session_id = session_id

    @classmethod
    def with_timeout(cls, session_id: UUID) -> "ReviewInviteView":
        """Фабричный метод для создания вьюшки с таймаутом при отправке в канал."""
        inst = cls(session_id=session_id)
        inst.timeout = _INVITE_TIMEOUT
        return inst

    async def on_timeout(self) -> None:
        """При истечении таймаута отменяем все оставшиеся CREATED-отзывы."""
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
                    except Exception as e:
                        logger.warning(
                            "[ReviewInviteView] Could not cancel review %s: %s", review.id, e
                        )
        except Exception as e:
            logger.error("[ReviewInviteView] on_timeout error: %s", e)

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

        # Получаем game_id из сессии
        async with game_review_service_ctx() as svc:
            session = await svc.session_repo.get_by_id(session_id)
            if not session:
                await inter.followup.send("❌ Сессия не найдена.", ephemeral=True)
                return

        # Создаём отзыв или переиспользуем существующий CREATED
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
                await inter.followup.send(
                    "⚠️ Отзыв уже был отправлен или отменён.", ephemeral=True
                )
                return
            from app.domain.enums.review_status_enum import ReviewStatusEnum
            if existing.status != ReviewStatusEnum.CREATED:
                await inter.followup.send(
                    "⚠️ Отзыв уже был отправлен или отменён.", ephemeral=True
                )
                return
            review = Mapper.entity_to_dto(existing, GameReviewResponseDTO)
        except GameReviewNotAllowedException as e:
            await inter.followup.send(f"❌ {e}", ephemeral=True)
            return

        # Собираем attending_players: (UUID, login) для выбора лучшего игрока
        attending_players: list[tuple[UUID, str]] = []
        for did in attending:
            async with user_service_ctx() as u_svc:
                u = await u_svc.get_user_by_discord(did)
            attending_players.append((u.id, u.login))

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