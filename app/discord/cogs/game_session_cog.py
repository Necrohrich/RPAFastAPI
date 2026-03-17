# app/discord/cogs/game_session_cog.py
from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from app.discord.dependencies import game_session_service_ctx
from app.discord.utils.event_utils import (
    get_event_image_url,
    notify_game_channel,
    delete_message_safe,
)
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO

logger = logging.getLogger(__name__)


class GameSessionCog(commands.Cog):
    """
    Обрабатывает Discord Scheduled Events и привязывает их к игровым сессиям.

    Жизненный цикл:
        CREATE → автоматически создаёт GameSession (CREATED) если название
                  события содержит название игры (ILIKE).
        UPDATE → синхронизирует title / description / image_url;
                  при отмене события — переводит сессию в CANCELED.
        START → если сессия ACTIVE (запущена через сайт) — применяет роли
                  из discord_state; иначе — показывает AttendanceView (6.5).
        END → завершает сессию, возвращает ники, удаляет временную роль (6.5).

    Исключения из сервисного слоя не перехватываются вручную — они логируются
    на уровне listener'а и не влияют на работу бота в целом.
    """

    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    # ── on_scheduled_event_create ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: disnake.GuildScheduledEvent) -> None:
        """
        Автоматически создаёт GameSession при создании Discord Scheduled Event.

        Алгоритм:
            1. Ищем игру, чьё название содержится в заголовке события (ILIKE).
            2. Если найдена — создаём сессию CREATED с привязкой discord_event_id.
            3. Если не найдена — логируем INFO и выходим.
        """
        logger.info(
            "[event_create] id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

        async with game_session_service_ctx() as service:
            game_id = await service.repo.find_game_id_by_event_title(event.name)

            if game_id is None:
                logger.info(
                    "[event_create] No game matched for %r — skipping", event.name
                )
                return

            # Guard: событие уже привязано (race condition при параллельных create)
            if await service.repo.get_by_discord_event_id(event.id):
                logger.info(
                    "[event_create] Event %s already linked — skipping", event.id
                )
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
        """
        Синхронизирует данные сессии при изменении Discord события.

        - Обновляет title / description / image_url при изменении.
        - При отмене события (status → canceled) переводит сессию в CANCELED
          и удаляет сообщение AttendanceView, если оно ещё висит.
        """
        logger.info(
            "[event_update] id=%s status=%s→%s",
            after.id, before.status, after.status,
        )

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(after.id)
            if not session:
                return

            # ── Отмена Discord-события ───────────────────────────────────────
            if (
                after.status == disnake.GuildScheduledEventStatus.canceled
                and before.status != disnake.GuildScheduledEventStatus.canceled
            ):
                # Берём state ДО cancel — сервис удаляет его внутри
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
                logger.info(
                    "[event_update] Session %s updated: %s",
                    session.id, list(changed.keys()),
                )

    # ── on_scheduled_event_start ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_scheduled_event_start(self, event: disnake.GuildScheduledEvent) -> None:
        """
        Обрабатывает старт Discord Scheduled Event.

        Сценарий A — сессия уже ACTIVE (запущена через сайт):
            discord_state существует → пропускаем AttendanceView,
            выдаём роли по данным из discord_state (TODO 6.5).

        Сценарий B — сессия ещё CREATED:
            Показываем AttendanceView в discord_main_channel_id (TODO 6.5),
            после завершения View — стартуем сессию и выдаём роли.
        """
        logger.info(
            "[event_start] id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

        async with game_session_service_ctx() as service:
            session = await service.repo.get_by_discord_event_id(event.id)
            if not session:
                logger.info("[event_start] No session linked to event %s — skipping", event.id)
                return

            game = await service.game_repo.get_by_id(session.game_id)
            discord_state = await service.repo.get_discord_state(session.id)

            # ── Сценарий A: сессия уже запущена через сайт ──────────────────
            if discord_state is not None:
                logger.info(
                    "[event_start] Session %s already active (via site), "
                    "applying roles from discord_state",
                    session.id,
                )
                attending_user_ids = discord_state.get("attending_user_ids", [])

                # TODO 6.5 — вызов:
                # await assign_session_roles(event.guild, game, attending_user_ids, discord_state, service)
                logger.info(
                    "[event_start] [TODO 6.5] assign_session_roles for %d users",
                    len(attending_user_ids),
                )

                if game:
                    await notify_game_channel(
                        self.bot,
                        channel_id=game.discord_main_channel_id,
                        role_id=game.discord_role_id,
                        text=f"🎲 Сессия #{session.session_number} началась!",
                        color=disnake.Color.green(),
                    )
                return

            # ── Сценарий B: нужен AttendanceView ────────────────────────────
            channel_id = game.discord_main_channel_id if game else None
            channel = self.bot.get_channel(channel_id) if channel_id else None

            if not channel:
                logger.warning(
                    "[event_start] No discord_main_channel_id for game %s "
                    "— starting with empty attendance",
                    session.game_id,
                )
                await service.start(session.id, attending_user_ids=[])
                logger.info("[event_start] Session %s started (no channel)", session.id)
                return

            # TODO 6.5 — создать и отправить AttendanceView:
            #
            #   view = AttendanceView(session=session, game=game, timeout=ATTENDANCE_TIMEOUT_SECONDS)
            #   msg = await channel.send(embed=build_attendance_embed(session, game), view=view)
            #
            #   # Сохраняем id сообщения сразу (нужно при отмене через on_scheduled_event_update)
            #   await service.repo.create_discord_state(
            #       session_id=session.id,
            #       attendance_message_id=msg.id,
            #   )
            #
            #   await view.wait()
            #   attending_user_ids: list[int] = view.result
            #
            #   await service.start(session.id, attending_user_ids=attending_user_ids)
            #   await assign_session_roles(event.guild, game, attending_user_ids, ..., service)

            logger.info(
                "[event_start] [TODO 6.5] AttendanceView stub — "
                "starting session %s with empty attendance",
                session.id,
            )
            await service.start(session.id, attending_user_ids=[])

            if game:
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
        """
        Обрабатывает окончание Discord Scheduled Event.

        1. Снимаем discord_state ДО complete (сервис удаляет его внутри).
        2. Завершаем сессию.
        3. Восстанавливаем ники и удаляем временную роль (TODO 6.5).
        """
        logger.info(
            "[event_end] id=%s title=%r guild=%s",
            event.id, event.name, event.guild_id,
        )

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

            if discord_state:
                # TODO 6.5 — вызов:
                # await restore_after_session(event.guild, discord_state)
                logger.info(
                    "[event_end] [TODO 6.5] restore_after_session, temp_role=%s",
                    discord_state.get("temp_role_id"),
                )

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