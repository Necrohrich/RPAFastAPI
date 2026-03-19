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
    user_service_ctx,
)
from app.discord.embeds.reviews.build_review_publish_embed import (
    build_review_publish_embed,
    build_review_publish_stats_header,
)
from app.discord.embeds.reviews.build_review_stats_embed import (
    build_npc_stats_embed,
    build_players_stats_embed,
    build_rating_stats_embed,
    build_scenes_stats_embed,
)
from app.discord.policies import require_role
from app.discord.utils.review_utils import send_review_invite, create_reviews_for_session, get_games_for_user, \
    get_author_discord_id, get_sessions_for_game, publish_reviews, select_game_wizard
from app.discord.views import SelectView
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
        """
        Кастомное событие, которое должен диспатчить GameSessionCog
        после успешного complete().

        Параметры:
            session — GameSessionResponseDTO
            game    — Game entity (domain) или GameResponseDTO; нужны
                      game_id, gm_id, discord_main_channel_id, discord_role_id, name
        """
        logger.info(
            "[review] on_session_completed fired for session %s", session.id
        )

        # Читаем discord_state (не удалялся при complete() — это намеренно)
        async with game_session_service_ctx() as svc:
            discord_state = await svc.get_discord_state(session.id)

        attending_discord_ids: list[int] = []
        if discord_state:
            attending_discord_ids = discord_state.get("attending_user_ids") or []

        # Создаём CREATED-отзывы для присутствовавших
        await create_reviews_for_session(session, attending_discord_ids)

        # Отправляем приглашение
        await send_review_invite(self.bot, session, game, attending_discord_ids)

    # ── /review ───────────────────────────────────────────────────────────────

    @commands.slash_command(name="review", description="Команды для игровых отзывов")
    async def review(self, inter: disnake.ApplicationCommandInteraction) -> None: ...

    # ── Модераторские операции ────────────────────────────────────────────────

    @review.sub_command(name="soft_delete", description="Мягко удалить отзыв [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def soft_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        review_id: str = commands.Param(description="UUID отзыва"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        async with game_review_service_ctx() as svc:
            await svc.soft_delete(UUID(review_id))
        await inter.followup.send("✅ Отзыв мягко удалён.", ephemeral=True)

    @review.sub_command(name="delete", description="Безвозвратно удалить отзыв [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def hard_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        review_id: str = commands.Param(description="UUID отзыва"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        async with game_review_service_ctx() as svc:
            await svc.delete(UUID(review_id))
        await inter.followup.send("✅ Отзыв безвозвратно удалён.", ephemeral=True)

    @review.sub_command(name="restore", description="Восстановить мягко удалённый отзыв [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def restore(
        self,
        inter: disnake.ApplicationCommandInteraction,
        review_id: str = commands.Param(description="UUID отзыва"),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        async with game_review_service_ctx() as svc:
            await svc.restore(UUID(review_id))
        await inter.followup.send("✅ Отзыв восстановлен.", ephemeral=True)

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
        author_id = await get_author_discord_id(author)
        if not author_id:
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
                await publish_reviews(
                    s_inter, sid,
                    sess.session_number if sess else 0,
                    game.name,
                    ReviewAnonymityEnum.PUBLIC,
                )

            # У GameSessionResponseDTO нет .name, используем title как display
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
        author_id = await get_author_discord_id(author)
        if not author_id:
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
                await publish_reviews(
                    s_inter, sid,
                    sess.session_number if sess else 0,
                    game.name,
                    ReviewAnonymityEnum.PRIVATE,
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
        author_id = await get_author_discord_id(author)
        if not author_id:
            return

        games = await get_games_for_user(author_id)
        if not games:
            await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
            return

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                reviews = await svc.get_list_by_game_id(
                    gid, statuses=[ReviewStatusEnum.SEND]
                )

            filtered = [r for r in reviews if r.anonymity == ReviewAnonymityEnum.PUBLIC]
            if not filtered:
                await cb_inter.followup.send("❌ Нет публичных отзывов.", ephemeral=True)
                return

            await inter.channel.send(
                embed=build_review_publish_stats_header(0, game.name, len(filtered))
            )
            for review in filtered:
                async with user_service_ctx() as u_svc:
                    u = await u_svc.get_by_id(review.user_id)
                author_discord_id = u.primary_discord_id
                await inter.channel.send(
                    embed=build_review_publish_embed(
                        review, session_number=0, game_name=game.name,
                        author_discord_id=author_discord_id,
                    )
                )
            await cb_inter.followup.send(
                f"✅ Опубликовано {len(filtered)} отзывов.", ephemeral=True
            )

        view = SelectView(
            items=games,
            display_field="name",
            title="Выберите игру",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)

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
        author_id = await get_author_discord_id(author)
        if not author_id:
            return

        games = await get_games_for_user(author_id)
        if not games:
            await inter.followup.send("❌ У пользователя нет игр.", ephemeral=True)
            return

        async def on_game_selected(cb_inter: disnake.MessageInteraction, game_id: str) -> None:
            gid = UUID(game_id)
            async with game_service_ctx() as gs:
                game = await gs.get_by_id(gid)
            async with game_review_service_ctx() as svc:
                reviews = await svc.get_list_by_game_id(
                    gid, statuses=[ReviewStatusEnum.SEND]
                )

            filtered = [r for r in reviews if r.anonymity == ReviewAnonymityEnum.PRIVATE]
            if not filtered:
                await cb_inter.followup.send("❌ Нет анонимных отзывов.", ephemeral=True)
                return

            await inter.channel.send(
                embed=build_review_publish_stats_header(0, game.name, len(filtered))
            )
            for review in filtered:
                await inter.channel.send(
                    embed=build_review_publish_embed(
                        review, session_number=0, game_name=game.name,
                        author_discord_id=None,
                    )
                )
            await cb_inter.followup.send(
                f"✅ Опубликовано {len(filtered)} анонимных отзывов.", ephemeral=True
            )

        view = SelectView(
            items=games,
            display_field="name",
            title="Выберите игру",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)

    # ── Статистика ────────────────────────────────────────────────────────────

    @review.sub_command(
        name="stats_scenes",
        description="Статистика сцен по игре [SUPPORT+]",
    )
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

    @review.sub_command(
        name="stats_npc",
        description="Статистика НИП по игре [SUPPORT+]",
    )
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

    @review.sub_command(
        name="stats_players",
        description="Статистика лучших игроков по игре [SUPPORT+]",
    )
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

    @review.sub_command(
        name="stats_rating",
        description="Взвешенная оценка игры [SUPPORT+]",
    )
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