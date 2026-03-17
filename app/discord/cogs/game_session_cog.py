# app/discord/cogs/game_session_cog.py
from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from app.discord.dependencies import game_session_service_ctx, guild_settings_service_ctx
from app.discord.utils.event_utils import (
    get_event_image_url,
    notify_game_channel,
    delete_message_safe,
)
from app.discord.utils.session_roles import assign_session_roles, restore_after_session
from app.discord.views.attendance_view import AttendanceView
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO
from app.exceptions import GuildSettingsNotFoundException

logger = logging.getLogger(__name__)


async def _get_role_anchor(guild_id: int) -> int | None:
    """Возвращает role_position_anchor_id из настроек гильдии или None."""
    try:
        async with guild_settings_service_ctx() as settings_service:
            settings = await settings_service.get(guild_id)
            return settings.role_position_anchor_id
    except GuildSettingsNotFoundException:
        return None


class GameSessionCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    # ── on_scheduled_event_create ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: disnake.GuildScheduledEvent) -> None:
        logger.info("[event_create] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        async with game_session_service_ctx() as service:
            game_id = await service.repo.find_game_id_by_event_title(event.name)
            if game_id is None:
                logger.info("[event_create] No game matched for %r — skipping", event.name)
                return

            if await service.repo.get_by_discord_event_id(event.id):
                logger.info("[event_create] Event %s already linked — skipping", event.id)
                return

            dto = CreateGameSessionDTO(
                game_id=game_id,
                discord_event_id=event.id,
                title=event.name,
                description=event.description or "",
                image_url=get_event_image_url(event),
            )
            session = await service.create(dto)
            logger.info(
                "[event_create] Session %s (#%s) created for game %s",
                session.id, session.session_number, game_id,
            )

            game = await service.game_repo.get_by_id(game_id)
            if game:
                await notify_game_channel(
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
        logger.info("[event_update] id=%s status=%s→%s", after.id, before.status, after.status)

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(after.id)
            if not session:
                return

            # ── Отмена ──────────────────────────────────────────────────────
            if (
                after.status == disnake.GuildScheduledEventStatus.canceled
                and before.status != disnake.GuildScheduledEventStatus.canceled
            ):
                discord_state = await service.repo.get_discord_state(session.id)
                game = await service.game_repo.get_by_id(session.game_id)

                await service.cancel(session.id)
                logger.info("[event_update] Session %s canceled", session.id)

                if discord_state and discord_state.get("attendance_message_id"):
                    await delete_message_safe(
                        self.bot,
                        channel_id=game.discord_main_channel_id if game else None,
                        message_id=discord_state["attendance_message_id"],
                    )

                if game:
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"❌ Сессия #{session.session_number} отменена",
                        color=disnake.Color.red(),
                    )
                return

            # ── Обновление полей ─────────────────────────────────────────────
            changed: dict = {}
            if after.name != (session.title or ""):
                changed["title"] = after.name
            if (after.description or "") != (session.description or ""):
                changed["description"] = after.description or ""
            new_image = get_event_image_url(after)
            if new_image != (session.image_url or ""):
                changed["image_url"] = new_image

            if changed:
                await service.update(session.id, UpdateGameSessionDTO(**changed))
                logger.info("[event_update] Session %s updated: %s", session.id, list(changed.keys()))

    # ── on_scheduled_event_start ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_start(self, event: disnake.GuildScheduledEvent) -> None:
        logger.info("[event_start] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info("[event_start] No session linked to event %s — skipping", event.id)
                return

            game = await service.game_repo.get_by_id(session.game_id)
            discord_state = await service.repo.get_discord_state(session.id)

            # ── Сценарий A: сессия уже запущена через сайт ──────────────────
            if discord_state is not None:
                logger.info("[event_start] Session %s already active (via site)", session.id)
                attending_ids: list[int] = discord_state.get("attending_user_ids", [])
                if game:
                    anchor = await _get_role_anchor(event.guild_id)
                    char_names = await service.repo.get_player_characters(game.id, attending_ids)
                    await assign_session_roles(
                        event.guild, game, session, attending_ids, char_names, anchor, service
                    )
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )
                return

            # ── Сценарий B: AttendanceView ───────────────────────────────────
            channel_id = game.discord_main_channel_id if game else None
            channel = self.bot.get_channel(channel_id) if channel_id else None

            if not channel:
                logger.warning(
                    "[event_start] No channel for game %s — starting with empty attendance",
                    session.game_id,
                )
                await service.start(session.id, attending_user_ids=[])
                return

            player_entries = await service.repo.get_accepted_players_with_discord(session.game_id)

            if not player_entries:
                logger.info("[event_start] No players with discord_id for game %s", session.game_id)
                await service.start(session.id, attending_user_ids=[])
                if game:
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )
                return

            gm_discord_id = game.gm_id if game else None
            if not gm_discord_id:
                logger.warning("[event_start] No gm_id for game %s — all players present", session.game_id)
                all_ids = [did for did, _ in player_entries]
                await service.start(session.id, attending_user_ids=all_ids)
                if game:
                    anchor = await _get_role_anchor(event.guild_id)
                    char_names = await service.repo.get_player_characters(game.id, all_ids)
                    await assign_session_roles(event.guild, game, session, all_ids, char_names, anchor, service)
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )
                return

            # Отправляем AttendanceView
            view = AttendanceView(
                session=session,
                game=game,
                player_entries=player_entries,
                gm_discord_id=gm_discord_id,
            )
            msg = await channel.send(embed=view.current_embed(), view=view)
            view.set_message(msg)

            # Сохраняем attendance_message_id — нужно при отмене через on_scheduled_event_update
            await service.repo.create_discord_state(
                session_id=session.id,
                attendance_message_id=msg.id,
            )
            logger.info("[event_start] AttendanceView sent, session=%s msg=%s", session.id, msg.id)

        # view.wait() — ВНЕ контекста service: UoW не должен висеть открытым 30 минут
        await view.wait()

        async with game_session_service_ctx() as service:
            # Перечитываем — сессия могла быть отменена пока висел View
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info("[event_start] Session canceled during AttendanceView — skipping start")
                return

            attending_ids = view.attending_ids
            await service.start(session.id, attending_user_ids=attending_ids)
            logger.info("[event_start] Session %s started, attending=%d", session.id, len(attending_ids))

            game = await service.game_repo.get_by_id(session.game_id)
            if game:
                anchor = await _get_role_anchor(event.guild_id)
                char_names = await service.repo.get_player_characters(game.id, attending_ids)
                await assign_session_roles(event.guild, game, session, attending_ids, char_names, anchor, service)
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"🎲 Сессия #{session.session_number} началась!",
                    color=disnake.Color.green(),
                )

    # ── on_scheduled_event_end ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_end(self, event: disnake.GuildScheduledEvent) -> None:
        logger.info("[event_end] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info("[event_end] No session linked to event %s — skipping", event.id)
                return

            # Берём state ДО complete — сервис удалит его внутри
            discord_state = await service.repo.get_discord_state(session.id)
            game = await service.game_repo.get_by_id(session.game_id)

            await service.complete(session.id)
            logger.info("[event_end] Session %s completed", session.id)

        # restore вызываем вне UoW — работает только с Discord API
        if discord_state:
            await restore_after_session(event.guild, discord_state)

        if game:
            await notify_game_channel(
                self.bot,
                channel_id=game.discord_main_channel_id,
                role_id=game.discord_role_id,
                text=f"✅ Сессия #{session.session_number} завершена",
                color=disnake.Color.green(),
            )


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(GameSessionCog(bot))
    logger.info("GameSessionCog loaded")