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
from app.discord.views import SelectView, ReviewInviteView
from app.domain.enums import ReviewAnonymityEnum, ReviewStatusEnum
from app.dto import GameReviewResponseDTO

logger = logging.getLogger(__name__)

async def send_review_invite(
    bot: commands.InteractionBot,
    session,           # GameSessionResponseDTO
    game,              # GameResponseDTO / Game entity — нужны name, discord_main_channel_id, discord_role_id, gm_id
    attending_user_ids_discord: list[int],
) -> None:
    """
    Отправляет вьюшку приглашения к отзыву.

    Если у игры есть discord_main_channel_id — шлём туда с пингом роли.
    Иначе — рассылаем по личке каждому игроку из attending_user_ids_discord.
    """
    embed = build_review_invite_embed(session, game.name)
    view = ReviewInviteView()

    channel_id = getattr(game, "discord_main_channel_id", None)
    role_id = getattr(game, "discord_role_id", None)

    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            content = f"<@&{role_id}>" if role_id else None
            try:
                await channel.send(content=content, embed=embed, view=view)
                logger.info(
                    "[review_invite] Sent invite to channel %s for session %s",
                    channel_id, session.id,
                )
                return
            except disnake.HTTPException as exc:
                logger.warning(
                    "[review_invite] Failed to send to channel %s: %s", channel_id, exc
                )

    # Fallback: личные сообщения каждому игроку
    for discord_id in attending_user_ids_discord:
        try:
            user = bot.get_user(discord_id)
            if user is None:
                user = await bot.fetch_user(discord_id)
            await user.send(embed=embed, view=view)
        except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException) as exc:
            logger.warning(
                "[review_invite] Could not DM player %s: %s", discord_id, exc
            )


async def create_reviews_for_session(
    session,
    attending_user_ids_discord: list[int],
) -> None:
    """
    Создаёт CREATED-отзывы для всех присутствовавших игроков.

    Конвертирует discord_id → UUID через user_service,
    затем вызывает review_service.create_for_session.
    """
    user_uuids: list[UUID] = []
    for discord_id in attending_user_ids_discord:
        async with user_service_ctx() as u_svc:
            u = await u_svc.get_user_by_discord(discord_id)
        user_uuids.append(u.id)

    if not user_uuids:
        return

    async with game_review_service_ctx() as svc:
        await svc.create_for_session(
            game_id=session.game_id,
            session_id=session.id,
            attending_user_ids=user_uuids,
        )

async def get_author_discord_id(
    user: User,
) -> UUID | None:
    """Возвращает UUID пользователя по discord User или None при ошибке."""
    async with user_service_ctx() as u_svc:
        u = await u_svc.get_user_by_discord(user.id)
    return u.id

async def get_games_for_user(author_id: UUID) -> list:
    async with game_service_ctx() as gs:
        return await gs.get_list_by_author_id(author_id)

async def get_sessions_for_game(game_id: UUID) -> list:
    """Возвращает все сессии игры (простой список для SelectView)."""
    async with game_session_service_ctx() as svc:
        result = await svc.get_by_game_id(game_id, page=1, page_size=200)
    return result.items

async def publish_reviews(
    inter: disnake.ApplicationCommandInteraction,
    session_id: UUID,
    session_number: int,
    game_name: str,
    anonymity: ReviewAnonymityEnum,
) -> None:
    """Публикует отзывы указанной сессии в текущий канал."""
    async with game_review_service_ctx() as svc:
        reviews = await svc.get_list_by_session_id(
            session_id,
            statuses=[ReviewStatusEnum.SEND],
        )

    filtered: list[GameReviewResponseDTO] = [
        r for r in reviews if r.anonymity == anonymity
    ]

    if not filtered:
        await inter.followup.send(
            f"❌ Нет {'публичных' if anonymity == ReviewAnonymityEnum.PUBLIC else 'анонимных'} "
            f"отзывов для этой сессии.",
            ephemeral=True,
        )
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
        await inter.channel.send(
            embed=build_review_publish_embed(
                review,
                session_number=session_number,
                game_name=game_name,
                author_discord_id=author_discord_id,
            )
        )

    await inter.followup.send(
        f"✅ Опубликовано {len(filtered)} отзывов.", ephemeral=True
    )

async def select_game_wizard(
    inter: disnake.ApplicationCommandInteraction,
    author: User,
    on_game_selected,
) -> None:
    """Переиспользуемый wizard: выбрать игру по автору."""
    author_id = await get_author_discord_id(author)
    if not author_id:
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