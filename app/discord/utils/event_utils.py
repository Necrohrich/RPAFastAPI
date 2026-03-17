# app/discord/utils/event_utils.py
from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


def get_event_image_url(event: disnake.GuildScheduledEvent) -> str:
    """
    Возвращает URL обложки события или пустую строку.

    Использует getattr для совместимости с разными версиями disnake:
    атрибут cover_image появился в disnake 2.x, но IDE может его не видеть
    если stubs устарели или установлена старая версия пакета.
    """
    image: disnake.Asset | None = getattr(event, "cover_image", None)
    if image is not None:
        return image.url
    return ""


async def notify_game_channel(
    bot: commands.InteractionBot,
    channel_id: int | None,
    role_id: int | None,
    text: str,
    color: disnake.Color = disnake.Color.blurple(),
) -> None:
    """
    Отправляет embed-уведомление в игровой канал с опциональным пингом роли.

    Используется при переходах статуса сессии (CREATED / ACTIVE / COMPLETED / CANCELED).
    Молча логирует ошибки — не бросает исключений.
    """
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.warning("notify_game_channel: channel %s not found in cache", channel_id)
        return
    embed = disnake.Embed(description=text, color=color)
    content = f"<@&{role_id}>" if role_id else None
    try:
        await channel.send(content=content, embed=embed)
    except disnake.HTTPException as exc:
        logger.error(
            "notify_game_channel: failed to send to channel %s: %s", channel_id, exc
        )


async def delete_message_safe(
    bot: commands.InteractionBot,
    channel_id: int | None,
    message_id: int | None,
) -> None:
    """
    Удаляет сообщение (AttendanceView и т.п.) без исключений.

    Используется при отмене/инвалидации сессии для очистки View в канале.
    """
    if not channel_id or not message_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    try:
        msg = await channel.fetch_message(message_id)
        await msg.delete()
    except (disnake.NotFound, disnake.HTTPException):
        pass