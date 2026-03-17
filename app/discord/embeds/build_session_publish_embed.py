# app/discord/embeds/build_session_publish_embed.py
import disnake

from app.dto import GameSessionResponseDTO


def build_session_publish_embed(session: GameSessionResponseDTO) -> disnake.Embed:
    """
    Embed для публикации завершённой сессии командой /session publish.

    Отображает:
        - Номер и название сессии
        - Описание
        - Картинку (если есть)
        - Время начала и окончания (если есть)
    """
    embed = disnake.Embed(
        title=f"Сессия #{session.session_number} — {session.title or '—'}",
        description=session.description or "",
        color=disnake.Color.blurple(),
    )

    if session.image_url:
        embed.set_image(url=session.image_url)

    if session.started_at:
        embed.add_field(
            name="🕐 Начало",
            value=disnake.utils.format_dt(session.started_at, style="f"),
            inline=True,
        )

    if session.ended_at:
        embed.add_field(
            name="🏁 Конец",
            value=disnake.utils.format_dt(session.ended_at, style="f"),
            inline=True,
        )

    return embed