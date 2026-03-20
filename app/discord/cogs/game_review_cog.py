# app/discord/cogs/game_review_cog.py
"""
Cog для системы игровых отзывов.

Listener on_session_completed срабатывает при переходе сессии в COMPLETED.
Slash-команды: удаление, рестор, публикация отзывов, статистика.
"""
from __future__ import annotations

import logging
from uuid import UUID

import disnake
from disnake import User
from disnake.ext import commands

from app.discord.dependencies import (
    game_review_service_ctx,
    game_service_ctx,
    game_session_service_ctx,
)
from app.discord.embeds.reviews.build_review_stats_embed import (
    build_npc_stats_embed,
    build_players_stats_embed,
    build_rating_stats_embed,
    build_scenes_stats_embed,
)
from app.discord.policies import require_role
from app.discord.utils.review_utils import (
    send_review_invite,
    create_reviews_for_session,
    select_game_wizard, publish_session_wizard, publish_game_wizard, review_manage_wizard,
)
from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_status_enum import ReviewStatusEnum
from app.domain.policies import PlatformPolicies

logger = logging.getLogger(__name__)


class GameReviewCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    # ── Listener ──────────────────────────────────────────────────────────────

    @commands.Cog.listener("on_session_completed")
    async def on_session_completed(self, session, game) -> None:
        logger.info("[review] on_session_completed fired for session %s", session.id)

        async with game_session_service_ctx() as svc:
            discord_state = await svc.get_discord_state(session.id)

        attending_discord_ids: list[int] = []
        if discord_state:
            attending_discord_ids = discord_state.get("attending_user_ids") or []

        await create_reviews_for_session(session, attending_discord_ids)
        await send_review_invite(self.bot, session, game, attending_discord_ids)

    # ── /review ───────────────────────────────────────────────────────────────

    @commands.slash_command(name="review", description="Команды для игровых отзывов")
    async def review(self, inter: disnake.ApplicationCommandInteraction) -> None: ...

    # ── Модераторские операции через SelectView ───────────────────────────────

    @review.sub_command(name="soft_delete", description="Мягко удалить отзыв [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def soft_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор отзывов"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await review_manage_wizard(
            inter, author,
            action_label="мягко удалить",
            statuses=[ReviewStatusEnum.SEND, ReviewStatusEnum.CREATED],
            action=lambda svc, rid: svc.soft_delete(rid),
            success_msg="✅ Отзыв мягко удалён.",
        )

    @review.sub_command(name="delete", description="Безвозвратно удалить отзыв [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def hard_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор отзывов"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await review_manage_wizard(
            inter, author,
            action_label="безвозвратно удалить",
            statuses=[ReviewStatusEnum.SEND, ReviewStatusEnum.CREATED, ReviewStatusEnum.CANCELED],
            include_deleted=True,
            action=lambda svc, rid: svc.delete(rid),
            success_msg="✅ Отзыв безвозвратно удалён.",
        )

    @review.sub_command(name="restore", description="Восстановить мягко удалённый отзыв [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def restore(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор отзывов"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await review_manage_wizard(
            inter, author,
            action_label="восстановить",
            statuses=None,            # любой статус
            include_deleted=True,
            only_deleted=True,        # только мягко удалённые
            action=lambda svc, rid: svc.restore(rid),
            success_msg="✅ Отзыв восстановлен.",
        )

    # ── Публикация по сессии ──────────────────────────────────────────────────

    @review.sub_command(
        name="publish_session_public",
        description="Опубликовать публичные отзывы сессии [SUPPORT+]",
    )
    @require_role(PlatformPolicies.require_support)
    async def publish_session_public(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await publish_session_wizard(inter, author, ReviewAnonymityEnum.PUBLIC)

    @review.sub_command(
        name="publish_session_anon",
        description="Опубликовать анонимные отзывы сессии [MODERATOR+]",
    )
    @require_role(PlatformPolicies.require_moderator)
    async def publish_session_anon(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await publish_session_wizard(inter, author, ReviewAnonymityEnum.PRIVATE)

    # ── Публикация всех отзывов игры ──────────────────────────────────────────

    @review.sub_command(
        name="publish_game_public",
        description="Опубликовать все публичные отзывы игры [SUPPORT+]",
    )
    @require_role(PlatformPolicies.require_support)
    async def publish_game_public(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await publish_game_wizard(inter, author, ReviewAnonymityEnum.PUBLIC)

    @review.sub_command(
        name="publish_game_anon",
        description="Опубликовать все анонимные отзывы игры [MODERATOR+]",
    )
    @require_role(PlatformPolicies.require_moderator)
    async def publish_game_anon(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        await publish_game_wizard(inter, author, ReviewAnonymityEnum.PRIVATE)

    # ── Статистика ────────────────────────────────────────────────────────────

    @review.sub_command(name="stats_scenes", description="Статистика сцен по игре [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def stats_scenes(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                stats = await svc.get_stats_scenes(gid)
            await cb_inter.followup.send(
                embed=build_scenes_stats_embed(game.name, stats), ephemeral=True
            )

        await select_game_wizard(inter, author, on_game_selected)

    @review.sub_command(name="stats_npc", description="Статистика НИП по игре [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def stats_npc(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                stats = await svc.get_stats_npc(gid)
            await cb_inter.followup.send(
                embed=build_npc_stats_embed(game.name, stats), ephemeral=True
            )

        await select_game_wizard(inter, author, on_game_selected)

    @review.sub_command(name="stats_players", description="Статистика лучших игроков по игре [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def stats_players(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                stats = await svc.get_stats_players(gid)
            await cb_inter.followup.send(
                embed=build_players_stats_embed(game.name, stats), ephemeral=True
            )

        await select_game_wizard(inter, author, on_game_selected)

    @review.sub_command(name="stats_rating", description="Взвешенная оценка игры [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def stats_rating(
        self,
        inter: disnake.ApplicationCommandInteraction,
        author: User = commands.Param(description="Автор игры"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                stats = await svc.get_stats_rating(gid)
            await cb_inter.followup.send(
                embed=build_rating_stats_embed(game.name, stats), ephemeral=True
            )

        await select_game_wizard(inter, author, on_game_selected)