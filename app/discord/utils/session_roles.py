# app/discord/utils/session_roles.py
from __future__ import annotations

import logging
import random

import disnake

from app.domain.entities import Game
from app.dto import GameSessionResponseDTO

logger = logging.getLogger(__name__)


async def assign_session_roles(
    guild: disnake.Guild,
    game: Game,
    session: GameSessionResponseDTO,
    attending_discord_ids: list[int],
    character_names: dict[int, str],  # {discord_id: character_name}
    role_position_anchor_id: int | None,
    service,  # GameSessionService — только для update_discord_state
) -> None:
    """
    Создаёт временную роль сессии, выдаёт её участникам и GM, переименовывает ники.

    Параметры:
        guild                   — Discord-сервер
        game                    — доменный объект игры (gm_id, discord_role_id, name)
        session                 — DTO сессии (id, session_number)
        attending_discord_ids   — список Discord ID присутствующих игроков (без GM)
        character_names         — {discord_id: имя персонажа} — для переименования ников
        role_position_anchor_id — ID роли-якоря для позиционирования (или None)
        service                 — GameSessionService для сохранения temp_role_id и original_nicknames
    """
    # ── Цвет роли ────────────────────────────────────────────────────────────
    role_color = disnake.Color.default()
    if game.discord_role_id:
        existing_role = guild.get_role(game.discord_role_id)
        if existing_role and existing_role.color != disnake.Color.default():
            role_color = existing_role.color
    if role_color == disnake.Color.default():
        role_color = disnake.Color(random.randint(0x100000, 0xFFFFFF))

    # ── Создаём временную роль ────────────────────────────────────────────────
    try:
        temp_role = await guild.create_role(
            name=game.name,
            color=role_color,
            hoist=True,
            reason=f"Сессия #{session.session_number} игры «{game.name}»",
        )
    except disnake.HTTPException as exc:
        logger.error("[session_roles] Failed to create temp role for game %s: %s", game.id, exc)
        return

    # ── Позиция роли над якорем ───────────────────────────────────────────────
    if role_position_anchor_id:
        anchor_role = guild.get_role(role_position_anchor_id)
        if anchor_role:
            try:
                await temp_role.edit(position=anchor_role.position + 1)
            except disnake.HTTPException as exc:
                logger.warning("[session_roles] Could not set role position: %s", exc)

    # ── Загружаем всех участников ────────────────────────────────────────────
    all_discord_ids: set[int] = set(attending_discord_ids)
    if game.gm_id:
        all_discord_ids.add(game.gm_id)

    members: dict[int, disnake.Member] = {}
    for discord_id in all_discord_ids:
        member = guild.get_member(discord_id)
        if member is None:
            try:
                member = await guild.fetch_member(discord_id)
            except (disnake.NotFound, disnake.HTTPException):
                logger.warning("[session_roles] Member %s not found in guild", discord_id)
                continue
        members[discord_id] = member

    # ── Сохраняем оригинальные ники и temp_role_id в discord_state ───────────
    original_nicknames = {str(did): m.display_name for did, m in members.items()}

    await service.repo.update_discord_state(
        session.id,
        temp_role_id=temp_role.id,
        original_nicknames=original_nicknames,
    )

    # ── Выдаём роль и переименовываем игроков ────────────────────────────────
    for discord_id in attending_discord_ids:
        member = members.get(discord_id)
        if not member:
            continue

        try:
            await member.add_roles(temp_role, reason="Начало сессии")
        except disnake.Forbidden:
            logger.warning("[session_roles] Cannot add role to member %s", discord_id)

        char_name = character_names.get(discord_id, "Игрок")
        try:
            await member.edit(nick=char_name[:32], reason="Начало сессии")
        except disnake.Forbidden:
            logger.warning("[session_roles] Cannot rename member %s", discord_id)

    # ── GM — роль + корона к нику ─────────────────────────────────────────────
    if game.gm_id:
        gm_member = members.get(game.gm_id)
        if gm_member:
            try:
                await gm_member.add_roles(temp_role, reason="Начало сессии")
            except disnake.Forbidden:
                logger.warning("[session_roles] Cannot add role to GM %s", game.gm_id)
            try:
                gm_nick = f"👑 {gm_member.display_name}"[:32]
                await gm_member.edit(nick=gm_nick, reason="Начало сессии — GM")
            except disnake.Forbidden:
                logger.warning("[session_roles] Cannot rename GM %s", game.gm_id)

    logger.info(
        "[session_roles] Assigned role %s to %d members for session %s",
        temp_role.id, len(members), session.id,
    )


async def restore_after_session(
    guild: disnake.Guild,
    discord_state: dict,
) -> None:
    """
    Восстанавливает ники участников и удаляет временную роль.

    Параметры:
        guild          — Discord-сервер
        discord_state  — dict с ключами temp_role_id и original_nicknames
    """
    temp_role_id: int | None = discord_state.get("temp_role_id")
    original_nicknames: dict[str, str] = discord_state.get("original_nicknames") or {}

    # ── Возвращаем ники ───────────────────────────────────────────────────────
    for discord_id_str, original_nick in original_nicknames.items():
        try:
            discord_id = int(discord_id_str)
            member = guild.get_member(discord_id)
            if member is None:
                member = await guild.fetch_member(discord_id)
            # None сбрасывает ник к имени аккаунта Discord
            await member.edit(
                nick=original_nick or None,
                reason="Конец сессии — восстановление ника",
            )
        except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException) as exc:
            logger.warning("[session_roles] Could not restore nick for %s: %s", discord_id_str, exc)

    # ── Удаляем временную роль ────────────────────────────────────────────────
    if temp_role_id:
        temp_role = guild.get_role(temp_role_id)
        if temp_role:
            try:
                await temp_role.delete(reason="Конец сессии")
                logger.info("[session_roles] Deleted temp role %s", temp_role_id)
            except disnake.HTTPException as exc:
                logger.warning("[session_roles] Could not delete temp role %s: %s", temp_role_id, exc)