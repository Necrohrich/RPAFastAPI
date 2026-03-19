# app/discord/views/reviews/review_invite_view.py
"""
Персистентная главная вьюшка приглашения к отзыву.

Footer формат: "session_id:{uuid}|game:{game_name}"

При нажатии «Оставить отзыв»:
1. Достаём session_id из footer.
2. Получаем user_id по discord_id нажавшего.
3. Создаём отзыв в БД (или переиспользуем существующий CREATED).
4. Конвертируем discord_state.attending_user_ids (list[int]) → list[tuple[UUID, str]]
   (uuid + login) за один проход здесь — передаём в ReviewFormView,
   чтобы кнопка «Игрок сессии» не делала повторных запросов.

Обработка ошибок делегирована BaseView.on_error → _handle_error.
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
from app.exceptions.game_review_exceptions import GameReviewAlreadyExistsException
from app.utils.mapper import Mapper

logger = logging.getLogger(__name__)


def _parse_footer(footer_text: str) -> tuple[UUID | None, str]:
    """Извлекает session_id и game_name из footer embed."""
    try:
        parts = dict(p.split(":", 1) for p in footer_text.split("|"))
        session_id = UUID(parts["session_id"])
        game_name = parts.get("game", "—")
        return session_id, game_name
    except Exception:
        return None, "—"


class ReviewInviteView(BaseView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @button(
        label="✅ Оставить отзыв",
        style=disnake.ButtonStyle.success,
        custom_id="review_invite:yes",
        row=0,
    )
    async def btn_yes(self, _: Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        session_id, _ = _parse_footer(
            inter.message.embeds[0].footer.text if inter.message.embeds else ""
        )
        if not session_id:
            await inter.followup.send("❌ Не удалось определить сессию.", ephemeral=True)
            return

        async with user_service_ctx() as user_svc:
            user_dto = await user_svc.get_user_by_discord(inter.author.id)

        user_id: UUID = user_dto.id

        # Создаём отзыв. Если уже существует CREATED — переиспользуем.
        # Остальные исключения (NotAllowed, NotFound и т.д.) уйдут в on_error.
        try:
            async with game_review_service_ctx() as svc:
                session = await svc.session_repo.get_by_id(session_id)
                if not session:
                    await inter.followup.send("❌ Сессия не найдена.", ephemeral=True)
                    return
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
            review = Mapper.entity_to_dto(existing, GameReviewResponseDTO)

        # Конвертируем attending discord_id (int) → (UUID, login) за один проход.
        # Пользователей без аккаунта в системе молча пропускаем — это не ошибка.
        attending_players: list[tuple[UUID, str]] = []
        async with game_review_service_ctx() as svc:
            discord_state = await svc.session_repo.get_discord_state(session_id)
        if discord_state:
            for did in (discord_state.get("attending_user_ids") or []):
                try:
                    async with user_service_ctx() as u_svc:
                        u = await u_svc.get_user_by_discord(did)
                    attending_players.append((u.id, u.login))
                except Exception:
                    # discord_id не привязан к аккаунту — пропускаем
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

        session_id, _ = _parse_footer(
            inter.message.embeds[0].footer.text if inter.message.embeds else ""
        )
        if not session_id:
            await inter.followup.send("🕊️ Хорошо, в другой раз!", ephemeral=True)
            return

        async with user_service_ctx() as user_svc:
            user_dto = await user_svc.get_user_by_discord(inter.author.id)

        async with game_review_service_ctx() as svc:
            existing = await svc.repo.get_by_session_id_and_user_id(
                session_id, user_dto.id, include_deleted=False
            )
            if existing and existing.status.value == "created":
                await svc.cancel(existing.id, user_dto.id)

        await inter.followup.send("🕊️ Хорошо, в другой раз!", ephemeral=True)