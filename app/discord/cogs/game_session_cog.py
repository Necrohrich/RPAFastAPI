# app/discord/cogs/game_session_cog.py
import logging
from uuid import UUID

import disnake
from disnake import User
from disnake.ext import commands

from app.discord.dependencies import (
    game_session_service_ctx,
    guild_settings_service_ctx,
    user_service_ctx,
    game_service_ctx,
)
from app.discord.embeds.build_session_publish_embed import build_session_publish_embed
from app.discord.policies import require_role
from app.discord.utils.event_utils import (
    get_event_image_url,
    notify_game_channel,
    delete_message_safe,
    create_session_for_event,
)
from app.discord.utils.session_roles import assign_session_roles, restore_after_session
from app.discord.views import AttendanceView, SelectView
from app.domain.enums import GameSessionStatusEnum
from app.domain.policies import PlatformPolicies
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO
from app.exceptions import GuildSettingsNotFoundException, GameSessionAlreadyActiveException

logger = logging.getLogger(__name__)


async def _get_role_anchor(guild_id: int) -> int | None:
    """Возвращает role_position_anchor_id из настроек гильдии или None."""
    try:
        async with guild_settings_service_ctx() as settings_service:
            settings = await settings_service.get(guild_id)
            return settings.role_position_anchor_id
    except GuildSettingsNotFoundException:
        return None


async def _delete_discord_event_safe(guild: disnake.Guild, discord_event_id: int) -> None:
    try:
        discord_event = await guild.fetch_scheduled_event(discord_event_id)
        await discord_event.delete()
        logger.info("[event_start] Duplicate discord event %s deleted", discord_event_id)
    except disnake.NotFound:
        pass
    except (disnake.HTTPException, OSError) as e:
        logger.warning("[event_start] Failed to delete duplicate discord event: %s", e)


class GameSessionCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    # ── on_guild_scheduled_event_create ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_scheduled_event_create(self, event: disnake.GuildScheduledEvent) -> None:
        logger.info("[event_create] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        async with game_session_service_ctx() as service:
            game_id = await service.find_game_id_by_event_title(event.name)
            if game_id is None:
                logger.info("[event_create] No game matched for %r — skipping", event.name)
                return

            existing = await service.get_session_by_event_id(event.id)
            if existing:
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

            game = await service.get_game_by_session(session.id)
            if game:
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"📅 Запланирована сессия #{session.session_number}: {session.title}",
                    color=disnake.Color.blue(),
                )

    # ── on_guild_scheduled_event_update ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(
        self,
        before: disnake.GuildScheduledEvent,
        after: disnake.GuildScheduledEvent,
    ) -> None:
        logger.info("[event_update] id=%s status=%s→%s", after.id, before.status, after.status)

        duplicate_event_id: int | None = None

        async with game_session_service_ctx() as service:
            session = await service.get_session_by_event_id(after.id)
            if not session:
                return

            if (
                after.status == disnake.GuildScheduledEventStatus.active
                and before.status != disnake.GuildScheduledEventStatus.active
            ):
                duplicate_event_id = await self._handle_event_start(after, service, session)

            elif (
                after.status == disnake.GuildScheduledEventStatus.completed
                and before.status != disnake.GuildScheduledEventStatus.completed
            ):
                await self._handle_event_end(after, service, session)

            else:
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

        if duplicate_event_id:
            await _delete_discord_event_safe(after.guild, duplicate_event_id)

    # ── on_guild_scheduled_event_delete ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(
            self,
            event: disnake.GuildScheduledEvent,
    ) -> None:
        logger.info("[event_delete] id=%s title=%r", event.id, event.name)
        async with game_session_service_ctx() as service:
            session = await service.get_session_by_event_id(event.id)
            if not session:
                return

            if session.status in (GameSessionStatusEnum.CANCELED, GameSessionStatusEnum.INVALID):
                logger.info("[event_delete] Session %s already %s — skipping", session.id, session.status)
                return

            game = await service.get_game_by_session(session.id)
            session_dto, discord_state = await service.cancel(session.id)
            logger.info("[event_delete] Session %s canceled", session.id)

            if discord_state and event.guild:
                await restore_after_session(event.guild, discord_state)

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
                    text=f"❌ Сессия #{session_dto.session_number} отменена",
                    color=disnake.Color.red(),
                )

    # ── _handle_event_start ───────────────────────────────────────────────────

    async def _handle_event_start(
        self, event: disnake.GuildScheduledEvent, service, session
    ) -> int | None:
        logger.info("[event_start] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        game = await service.get_game_by_session(session.id)
        discord_state = await service.get_discord_state(session.id)

        # ── Сценарий A: сессия уже запущена через сайт ──────────────────────
        if discord_state is not None:
            logger.info("[event_start] Session %s already active (via site)", session.id)
            attending_ids: list[int] = discord_state.get("attending_user_ids", [])
            if game:
                anchor = await _get_role_anchor(event.guild_id)
                char_names = await service.get_player_characters(session.id, attending_ids)
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
            return None

        async def _invalidate_duplicate(active_svc, duplicate_session, active_game) -> None:
            logger.warning(
                "[event_start] Session %s cannot start — active session exists for game %s",
                duplicate_session.id, duplicate_session.game_id,
            )
            await active_svc.invalidate(duplicate_session.id)
            if active_game:
                await notify_game_channel(
                    self.bot,
                    channel_id=active_game.discord_main_channel_id,
                    role_id=active_game.discord_role_id,
                    text=(
                        f"⚠️ Сессия #{duplicate_session.session_number} «{duplicate_session.title}» не может быть запущена — "
                        f"для игры **{active_game.name}** уже существует активная сессия.\n"
                        f"Сессия помечена как **INVALID**, событие в Discord удалено."
                    ),
                    color=disnake.Color.orange(),
                )

        # ── Сценарий B: нет канала ───────────────────────────────────────────
        channel_id = game.discord_main_channel_id if game else None
        channel = self.bot.get_channel(channel_id) if channel_id else None

        if not channel:
            logger.warning(
                "[event_start] No channel for game %s — starting with empty attendance",
                session.game_id,
            )
            try:
                await service.start(session.id, attending_user_ids=[])
            except GameSessionAlreadyActiveException:
                await _invalidate_duplicate(service, session, game)
                return session.discord_event_id
            return None

        # ── Сценарий C: нет игроков ──────────────────────────────────────────
        player_entries = await service.get_accepted_players_with_discord(session.id)

        if not player_entries:
            logger.info("[event_start] No players with discord_id for game %s", session.game_id)
            try:
                await service.start(session.id, attending_user_ids=[])
            except GameSessionAlreadyActiveException:
                await _invalidate_duplicate(service, session, game)
                return session.discord_event_id
            if game:
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"🎲 Сессия #{session.session_number} началась!",
                    color=disnake.Color.green(),
                )
            return None

        # ── Сценарий D: нет GM ───────────────────────────────────────────────
        gm_discord_id = game.gm_id if game else None
        if not gm_discord_id:
            logger.warning("[event_start] No gm_id for game %s — all players present", session.game_id)
            all_ids = [did for did, _ in player_entries]
            try:
                await service.start(session.id, attending_user_ids=all_ids)
            except GameSessionAlreadyActiveException:
                await _invalidate_duplicate(service, session, game)
                return session.discord_event_id
            if game:
                anchor = await _get_role_anchor(event.guild_id)
                char_names = await service.get_player_characters(session.id, all_ids)
                await assign_session_roles(event.guild, game, session, all_ids, char_names, anchor, service)
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"🎲 Сессия #{session.session_number} началась!",
                    color=disnake.Color.green(),
                )
            return None

        # ── Сценарий E: AttendanceView ───────────────────────────────────────
        view = AttendanceView(
            session=session,
            game=game,
            player_entries=player_entries,
            gm_discord_id=gm_discord_id,
        )
        msg = await channel.send(embed=view.current_embed(), view=view)
        view.set_message(msg)

        logger.info("[event_start] AttendanceView sent, session=%s msg=%s", session.id, msg.id)

        await view.wait()

        dup_event_id: int | None = None

        async with game_session_service_ctx() as svc:
            session = await svc.get_session_by_event_id(event.id)
            if not session:
                logger.info("[event_start] Session canceled during AttendanceView — skipping start")
                return None

            attending_ids = view.attending_ids
            try:
                await svc.start(session.id, attending_user_ids=attending_ids, attendance_message_id=msg.id)
            except GameSessionAlreadyActiveException:
                dup_event_id = session.discord_event_id
                await _invalidate_duplicate(svc, session, game)
            else:
                logger.info("[event_start] Session %s started, attending=%d", session.id, len(attending_ids))
                game = await svc.get_game_by_session(session.id)
                if game:
                    anchor = await _get_role_anchor(event.guild_id)
                    char_names = await svc.get_player_characters(session.id, attending_ids)
                    await assign_session_roles(event.guild, game, session, attending_ids, char_names, anchor, svc)
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )

        if dup_event_id:
            return dup_event_id

        return None

    # ── _handle_event_end ─────────────────────────────────────────────────────

    async def _handle_event_end(self, event: disnake.GuildScheduledEvent, service, session) -> None:
        logger.info("[event_end] id=%s title=%r guild=%s", event.id, event.name, event.guild_id)

        if session.status == GameSessionStatusEnum.INVALID:
            logger.info("[event_end] Session %s is INVALID — skipping", session.id)
            return

        discord_state = await service.get_discord_state(session.id)
        game = await service.get_game_by_session(session.id)

        await service.complete(session.id)
        logger.info("[event_end] Session %s completed", session.id)

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

    # ── /session ──────────────────────────────────────────────────────────────

    @commands.slash_command(name="session", description="Команды для управления игровыми сессиями")
    async def session(self, inter: disnake.ApplicationCommandInteraction) -> None: ...

    # ── /session link ─────────────────────────────────────────────────────────

    @session.sub_command(name="link", description="Создать сессию из Discord-события [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def session_link(
            self,
            inter: disnake.ApplicationCommandInteraction,
            discord_user: User,
            event_id: str = commands.Param(description="ID Discord Scheduled Event"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        try:
            discord_event_id = int(event_id)
        except ValueError:
            await inter.followup.send("❌ `event_id` должен быть числом.", ephemeral=True)
            return

        try:
            event = await inter.guild.fetch_scheduled_event(discord_event_id)
        except disnake.NotFound:
            await inter.followup.send("❌ Discord-событие не найдено.", ephemeral=True)
            return

        async with game_session_service_ctx() as service:
            existing = await service.get_session_by_event_id(discord_event_id)
            if existing:
                await inter.followup.send(
                    f"⚠️ Для события уже существует сессия "
                    f"**#{existing.session_number}** «{existing.title}».",
                    ephemeral=True,
                )
                return

            gid = await service.find_game_id_by_event_title(event.name)

        if gid:
            await create_session_for_event(self.bot, inter, event, gid)
            return

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(discord_user.id)

        async with game_service_ctx() as gs:
            games = await gs.get_list_by_author_id(user.id)

        if not games:
            await inter.followup.send(
                f"❌ Не удалось найти игру по названию «{event.name}».\n"
                f"У пользователя нет доступных игр.",
                ephemeral=True,
            )
            return

        async def on_game_selected(
                cb_inter: disnake.MessageInteraction, selected_game_id: str
        ) -> None:
            await create_session_for_event(self.bot, cb_inter, event, UUID(selected_game_id))

        view = SelectView(
            items=games,
            display_field="name",
            title="Выберите игру",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send(
            f"Игра не найдена автоматически по названию «{event.name}».\nВыберите игру:",
            view=view,
            ephemeral=True,
        )

    # ── /session cancel ───────────────────────────────────────────────────────

    @session.sub_command(name="cancel", description="Отменить игровую сессию [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def session_cancel(
            self,
            inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_session_service_ctx() as service:
            sessions = await service.get_non_invalid_list()
            sessions = [
                s for s in sessions
                if s.status in (GameSessionStatusEnum.CREATED, GameSessionStatusEnum.ACTIVE)
            ]

        if not sessions:
            await inter.followup.send(
                "❌ Нет активных или запланированных сессий для отмены.", ephemeral=True
            )
            return

        async def on_session_selected(
                cb_inter: disnake.MessageInteraction, selected_id: UUID
        ) -> None:
            async with game_session_service_ctx() as svc:
                session, discord_state = await svc.cancel(selected_id)
                game = await svc.get_game_by_session(session.id)

            if discord_state and inter.guild:
                await restore_after_session(inter.guild, discord_state)

            if discord_state and discord_state.get("attendance_message_id") and game:
                await delete_message_safe(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    message_id=discord_state["attendance_message_id"],
                )

            if session.discord_event_id and inter.guild:
                try:
                    discord_event = await inter.guild.fetch_scheduled_event(session.discord_event_id)
                    await discord_event.cancel()
                except disnake.NotFound:
                    pass
                except disnake.HTTPException as e:
                    logger.warning("[session_cancel] Failed to cancel discord event: %s", e)

            if game:
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"❌ Сессия #{session.session_number} «{session.title}» отменена.",
                    color=disnake.Color.red(),
                )

            await cb_inter.followup.send(
                f"✅ Сессия **#{session.session_number}** «{session.title}» отменена.",
                ephemeral=True,
            )

        view = SelectView(
            items=sessions,
            display_field="title",
            title="Выберите сессию для отмены",
            callback=on_session_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите сессию:", view=view, ephemeral=True)

    # ── /session invalidate ───────────────────────────────────────────────────

    @session.sub_command(name="invalidate", description="Пометить сессию как недействительную [MODERATOR+]")
    @require_role(PlatformPolicies.require_moderator)
    async def session_invalidate(
            self,
            inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_session_service_ctx() as service:
            sessions = await service.get_non_invalid_list()

        if not sessions:
            await inter.followup.send("❌ Нет сессий для инвалидации.", ephemeral=True)
            return

        async def on_session_selected(
                cb_inter: disnake.MessageInteraction, selected_id: UUID
        ) -> None:
            async with game_session_service_ctx() as svc:
                session, discord_state = await svc.invalidate(selected_id)
                game = await svc.get_game_by_session(session.id)

            if discord_state and inter.guild:
                await restore_after_session(inter.guild, discord_state)

            if discord_state and discord_state.get("attendance_message_id") and game:
                await delete_message_safe(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    message_id=discord_state["attendance_message_id"],
                )

            if game:
                await notify_game_channel(
                    self.bot,
                    channel_id=game.discord_main_channel_id,
                    role_id=game.discord_role_id,
                    text=f"⛔ Сессия #{session.session_number} «{session.title}» помечена как недействительная.",
                    color=disnake.Color.dark_grey(),
                )

            await cb_inter.followup.send(
                f"✅ Сессия **#{session.session_number}** «{session.title}» инвалидирована.",
                ephemeral=True,
            )

        view = SelectView(
            items=sessions,
            display_field="title",
            title="Выберите сессию для инвалидации",
            callback=on_session_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите сессию:", view=view, ephemeral=True)

    # ── /session publish ──────────────────────────────────────────────────────

    @session.sub_command(
        name="publish",
        description="Опубликовать завершённые сессии игры [SUPPORT+]"
    )
    @require_role(PlatformPolicies.require_support)
    async def session_publish(
            self,
            inter: disnake.ApplicationCommandInteraction,
            from_session: int = commands.Param(
                default=None,
                description="С какой сессии включительно (по умолчанию — только последняя)"
            ),
            to_session: int = commands.Param(
                default=None,
                description="По какую сессию включительно (по умолчанию — только последняя)"
            ),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with game_service_ctx() as gs:
            games = await gs.get_list_by_author_id(user.id)

        if not games:
            await inter.followup.send("❌ У вас нет игр.", ephemeral=True)
            return

        async def on_game_selected(
                cb_inter: disnake.MessageInteraction, selected_game_id: str
        ) -> None:
            gid = UUID(selected_game_id)

            async with game_session_service_ctx() as gsc:
                result = await gsc.get_completed_by_game_id(
                    game_id=gid,
                    page=1,
                    page_size=200,
                    from_number=from_session,
                    to_number=to_session,
                )

            sessions = result.items

            if from_session is None and to_session is None:
                sessions = sessions[-1:] if sessions else []
                range_text = "последняя завершённая сессия"
            else:
                parts = []
                if from_session:
                    parts.append(f"с #{from_session}")
                if to_session:
                    parts.append(f"по #{to_session}")
                range_text = " ".join(parts)

            if not sessions:
                await cb_inter.followup.send("❌ Завершённых сессий не найдено.", ephemeral=True)
                return

            for s in sessions:
                await inter.channel.send(embed=build_session_publish_embed(s))

            await cb_inter.followup.send(
                f"✅ Опубликовано {len(sessions)} сессий ({range_text}).\n"
                f"💡 Всего завершённых: **{result.total}**.",
                ephemeral=True,
            )

        view = SelectView(
            items=games,
            display_field="name",
            title="Выберите игру",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)

    # ── /session info ─────────────────────────────────────────────────────────

    @session.sub_command(name="info", description="Статистика сессий игры [SUPPORT+]")
    @require_role(PlatformPolicies.require_support)
    async def session_info(
            self,
            inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with game_service_ctx() as gs:
            games = await gs.get_list_by_author_id(user.id)

        if not games:
            await inter.followup.send("❌ У вас нет игр.", ephemeral=True)
            return

        async def on_game_selected(
                cb_inter: disnake.MessageInteraction, selected_game_id: str
        ) -> None:
            gid = UUID(selected_game_id)

            async with game_session_service_ctx() as gsc:
                game = await gsc.get_game_by_game_id(gid)
                total_all = await gsc.get_by_game_id(gid, page=1, page_size=1)
                completed = await gsc.get_completed_by_game_id(gid, page=1, page_size=1)
                active = await gsc.find_active_by_game_id(gid)
                last_valid = await gsc.get_last_valid_by_game_id(gid)

            embed = disnake.Embed(
                title=f"📊 Статистика сессий — {game.name}",
                color=disnake.Color.blurple(),
            )
            embed.add_field(name="Всего сессий", value=str(total_all.total), inline=True)
            embed.add_field(name="Завершённых", value=str(completed.total), inline=True)
            embed.add_field(
                name="Активная",
                value=f"#{active.session_number} «{active.title}»" if active else "нет",
                inline=True,
            )
            embed.add_field(
                name="Последняя действительная",
                value=f"#{last_valid.session_number} «{last_valid.title}»" if last_valid else "нет",
                inline=False,
            )
            if completed.total > 0:
                embed.set_footer(
                    text=f"Для публикации: /session publish "
                         f"[from_session:1 to_session:{last_valid.session_number if last_valid else '?'}]"
                )

            await cb_inter.followup.send(embed=embed, ephemeral=True)

        view = SelectView(
            items=games,
            display_field="name",
            title="Выберите игру",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)