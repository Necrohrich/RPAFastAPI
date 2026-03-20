# app/discord/utils/review_utils.py
import logging
from uuid import UUID

import disnake
from disnake import User
from disnake.ext import commands

from app.discord.dependencies import user_service_ctx, game_review_service_ctx, game_session_service_ctx, \
    game_service_ctx
from app.discord.embeds.reviews.build_review_invite_embed import build_review_invite_embed
from app.discord.embeds.reviews.build_review_publish_embed import build_review_publish_embed, \
    build_review_publish_stats_header
from app.discord.views import SelectView
from app.discord.views.reviews.review_invite_view import ReviewInviteView
from app.domain.enums import ReviewAnonymityEnum, ReviewStatusEnum
from app.dto import GameReviewResponseDTO
from app.exceptions import GameReviewNotFoundException
from app.exceptions.common_exceptions import NotFoundError

logger = logging.getLogger(__name__)


async def send_review_invite(
        bot: commands.InteractionBot,
        session,
        game,
        attending_user_ids_discord: list[int],
) -> None:
    embed = build_review_invite_embed(session, game.name)
    channel_id = getattr(game, "discord_main_channel_id", None)
    role_id = getattr(game, "discord_role_id", None)

    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            content = f"<@&{role_id}>" if role_id else None
            view = ReviewInviteView.with_timeout(session.id)
            try:
                msg = await channel.send(content=content, embed=embed, view=view)
                view.set_message(msg)
                logger.info("[review_invite] Sent invite to channel %s for session %s", channel_id, session.id)
                return
            except disnake.HTTPException as exc:
                logger.warning("[review_invite] Failed to send to channel %s: %s", channel_id, exc)

    # Fallback: личные сообщения каждому игроку — у каждого свой экземпляр view
    for discord_id in attending_user_ids_discord:
        try:
            user = bot.get_user(discord_id)
            if user is None:
                user = await bot.fetch_user(discord_id)
            view = ReviewInviteView.with_timeout(session.id)
            msg = await user.send(embed=embed, view=view)
            view.set_message(msg)
        except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException) as exc:
            logger.warning("[review_invite] Could not DM player %s: %s", discord_id, exc)


async def create_reviews_for_session(
    session,
    attending_user_ids_discord: list[int],
) -> None:
    user_uuids: list[UUID] = []
    for discord_id in attending_user_ids_discord:
        try:
            async with user_service_ctx() as u_svc:
                u = await u_svc.get_user_by_discord(discord_id)
            user_uuids.append(u.id)
        except (NotFoundError, Exception) as exc:  # noqa: BLE001
            logger.warning("[create_reviews] Could not resolve discord_id %s: %s", discord_id, exc)

    if not user_uuids:
        return

    async with game_review_service_ctx() as svc:
        await svc.create_for_session(
            game_id=session.game_id,
            session_id=session.id,
            attending_user_ids=user_uuids,
        )


async def get_author_discord_id(user: User) -> UUID | None:
    try:
        async with user_service_ctx() as u_svc:
            u = await u_svc.get_user_by_discord(user.id)
        return u.id
    except (NotFoundError, Exception) as exc:  # noqa: BLE001
        logger.warning("[review_utils] Could not resolve user %s: %s", user.id, exc)
        return None


async def get_games_for_user(author_id: UUID) -> list:
    async with game_service_ctx() as gs:
        return await gs.get_list_by_author_id(author_id)


async def get_sessions_for_game(game_id: UUID) -> list:
    async with game_session_service_ctx() as sess_svc:
        result = await sess_svc.get_by_game_id(game_id, page=1, page_size=200)
    return result.items


async def _resolve_best_player_login(review: GameReviewResponseDTO) -> str | None:
    if not review.best_player_id:
        return None
    try:
        async with user_service_ctx() as u_svc:
            bp = await u_svc.get_by_id(review.best_player_id)
        return bp.login
    except (NotFoundError, Exception) as exc:  # noqa: BLE001
        logger.warning("[review_utils] Could not resolve best_player %s: %s", review.best_player_id, exc)
        return None


async def _resolve_login(user_id: UUID) -> str:
    """Возвращает логин пользователя или усечённый UUID при ошибке."""
    try:
        async with user_service_ctx() as u_svc:
            u = await u_svc.get_by_id(user_id)
        return u.login
    except (NotFoundError, Exception) as exc:  # noqa: BLE001
        logger.warning("[review_utils] Could not resolve login for %s: %s", user_id, exc)
        return str(user_id)[:8]


async def publish_reviews_with_logins(
    inter: disnake.ApplicationCommandInteraction | disnake.MessageInteraction,
    session_id: UUID,
    session_number: int,
    game_name: str,
    anonymity: ReviewAnonymityEnum,
) -> None:
    async with game_review_service_ctx() as review_svc:
        reviews = await review_svc.get_list_by_session_id(
            session_id,
            statuses=[ReviewStatusEnum.SEND],
        )

    filtered: list[GameReviewResponseDTO] = [
        r for r in reviews if r.anonymity == anonymity
    ]

    label = "публичных" if anonymity == ReviewAnonymityEnum.PUBLIC else "анонимных"
    if not filtered:
        await inter.followup.send(f"❌ Нет {label} отзывов для этой сессии.", ephemeral=True)
        return

    await inter.channel.send(
        embed=build_review_publish_stats_header(session_number, game_name, len(filtered))
    )

    for review in filtered:
        author_discord_id: int | None = None
        if review.anonymity == ReviewAnonymityEnum.PUBLIC:
            async with user_service_ctx() as u_svc:
                u = await u_svc.get_by_id(review.user_id)
            author_discord_id = u.primary_discord_id

        best_player_login = await _resolve_best_player_login(review)

        await inter.channel.send(
            embed=build_review_publish_embed(
                review,
                session_number=session_number,
                game_name=game_name,
                author_discord_id=author_discord_id,
                best_player_login=best_player_login,
            )
        )

    await inter.followup.send(f"✅ Опубликовано {len(filtered)} {label} отзывов.", ephemeral=True)


async def select_game_wizard(
    inter: disnake.ApplicationCommandInteraction,
    author: User,
    on_game_selected,
) -> None:
    author_id = await get_author_discord_id(author)
    if not author_id:
        await inter.followup.send("❌ Пользователь не найден в системе.", ephemeral=True)
        return

    games = await get_games_for_user(author_id)
    if not games:
        await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
        return

    view = SelectView(
        items=games,
        display_field="name",
        title="Выберите игру",
        callback=on_game_selected,
        skippable=False,
    )
    await inter.followup.send("Выберите игру:", view=view, ephemeral=True)


async def publish_session_wizard(
    inter: disnake.ApplicationCommandInteraction,
    author: User,
    anonymity: ReviewAnonymityEnum,
) -> None:
    author_id = await get_author_discord_id(author)
    if not author_id:
        await inter.followup.send("❌ Пользователь не найден в системе.", ephemeral=True)
        return

    games = await get_games_for_user(author_id)
    if not games:
        await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
        return

    async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
        gid = UUID(game_id)
        sessions = await get_sessions_for_game(gid)
        if not sessions:
            await cb_inter.followup.send("❌ Нет сессий.", ephemeral=True)
            return

        async with game_service_ctx() as gs:
            game = await gs.get_by_id(gid)

        async def on_session_selected(
            s_inter: disnake.MessageInteraction, session_id: str
        ) -> None:
            sid = UUID(session_id)
            sess = next((s for s in sessions if str(s.id) == session_id), None)
            await publish_reviews_with_logins(
                s_inter, sid,
                sess.session_number if sess else 0,
                game.name,
                anonymity,
            )

        class _SessionItem:
            def __init__(self, s):
                self.id = s.id
                self.name = f"#{s.session_number} {s.title or '—'}"

        select_view = SelectView(
            items=[_SessionItem(s) for s in sessions],
            display_field="name",
            title="Выберите сессию",
            callback=on_session_selected,
            skippable=False,
        )
        await cb_inter.followup.send("Выберите сессию:", view=select_view, ephemeral=True)

    view = SelectView(
        items=games,
        display_field="name",
        title="Выберите игру",
        callback=on_game_selected,
        skippable=False,
    )
    await inter.followup.send("Выберите игру:", view=view, ephemeral=True)


async def publish_game_wizard(
    inter: disnake.ApplicationCommandInteraction,
    author: User,
    anonymity: ReviewAnonymityEnum,
) -> None:
    author_id = await get_author_discord_id(author)
    if not author_id:
        await inter.followup.send("❌ Пользователь не найден в системе.", ephemeral=True)
        return

    games = await get_games_for_user(author_id)
    if not games:
        await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
        return

    async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
        gid = UUID(game_id)
        async with game_service_ctx() as gs:
            game = await gs.get_by_id(gid)
        async with game_review_service_ctx() as review_svc:
            reviews = await review_svc.get_list_by_game_id(gid, statuses=[ReviewStatusEnum.SEND])

        filtered = [r for r in reviews if r.anonymity == anonymity]
        if not filtered:
            label = "публичных" if anonymity == ReviewAnonymityEnum.PUBLIC else "анонимных"
            await cb_inter.followup.send(f"❌ Нет {label} отзывов.", ephemeral=True)
            return

        await inter.channel.send(
            embed=build_review_publish_stats_header(0, game.name, len(filtered))
        )

        # Реальные номера сессий без неиспользуемой переменной context manager
        sessions = await get_sessions_for_game(gid)
        session_numbers: dict[UUID, int] = {s.id: s.session_number for s in sessions}

        for review in filtered:
            author_discord_id: int | None = None
            if anonymity == ReviewAnonymityEnum.PUBLIC:
                async with user_service_ctx() as u_svc:
                    u = await u_svc.get_by_id(review.user_id)
                author_discord_id = u.primary_discord_id

            best_player_login = await _resolve_best_player_login(review)
            s_number = session_numbers.get(review.session_id, 0)

            await inter.channel.send(
                embed=build_review_publish_embed(
                    review,
                    session_number=s_number,
                    game_name=game.name,
                    author_discord_id=author_discord_id,
                    best_player_login=best_player_login,
                )
            )

        await cb_inter.followup.send(f"✅ Опубликовано {len(filtered)} отзывов.", ephemeral=True)

    view = SelectView(
        items=games,
        display_field="name",
        title="Выберите игру",
        callback=on_game_selected,
        skippable=False,
    )
    await inter.followup.send("Выберите игру:", view=view, ephemeral=True)


class _ReviewItem:
    """Обёртка отзыва для SelectView. Принимает готовые значения, не shadowing внешних имён."""
    __slots__ = ("id", "name")

    def __init__(self, review_id: UUID, display_name: str) -> None:
        self.id = review_id
        self.name = display_name


async def review_manage_wizard(
    inter: disnake.ApplicationCommandInteraction,
    author: User,
    action_label: str,
    statuses: list[ReviewStatusEnum] | None,
    action,
    success_msg: str,
    include_deleted: bool = False,
    only_deleted: bool = False,
) -> None:
    """
    Общий wizard для управления отзывами: выбор игры → выбор отзыва → действие.
    only_deleted=True — показывает только мягко удалённые (для restore).
    """
    author_id = await get_author_discord_id(author)
    if not author_id:
        await inter.followup.send("❌ Пользователь не найден в системе.", ephemeral=True)
        return

    games = await get_games_for_user(author_id)
    if not games:
        await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
        return

    async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
        gid = UUID(game_id)
        async with game_review_service_ctx() as review_svc:
            if only_deleted:
                all_reviews = await review_svc.repo.get_list_by_game_id(
                    gid, statuses=statuses, include_deleted=True
                )
                reviews = [r for r in all_reviews if r.deleted_at is not None]
            else:
                reviews = await review_svc.get_list_by_game_id(
                    gid, statuses=statuses, include_deleted=include_deleted
                )

        if not reviews:
            await cb_inter.followup.send(
                f"❌ Нет отзывов для действия «{action_label}».", ephemeral=True
            )
            return

        items: list[_ReviewItem] = []
        for r in reviews:
            login = await _resolve_login(r.user_id)
            display_name = f"{login} | {r.status} | id:{str(r.id)[:8]}"
            items.append(_ReviewItem(r.id, display_name))

        async def on_review_selected(
            s_inter: disnake.MessageInteraction, review_id: str
        ) -> None:
            rid = UUID(review_id)
            try:
                async with game_review_service_ctx() as manage_svc:
                    await action(manage_svc, rid)
                await s_inter.followup.send(success_msg, ephemeral=True)
            except GameReviewNotFoundException:
                await s_inter.followup.send("❌ Отзыв не найден.", ephemeral=True)

        select_view = SelectView(
            items=items,
            display_field="name",
            title="Выберите отзыв",
            callback=on_review_selected,
            skippable=False,
        )
        await cb_inter.followup.send("Выберите отзыв:", view=select_view, ephemeral=True)

    view = SelectView(
        items=games,
        display_field="name",
        title="Выберите игру",
        callback=on_game_selected,
        skippable=False,
    )
    await inter.followup.send("Выберите игру:", view=view, ephemeral=True)