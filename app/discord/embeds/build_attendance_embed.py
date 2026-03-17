# app/discord/embeds/build_attendance_embed.py
import disnake

from app.domain.entities import Game
from app.dto import GameSessionResponseDTO


def build_attendance_embed(
    session: GameSessionResponseDTO,
    game: Game,
    current_name: str,
    current_index: int,
    total: int,
) -> disnake.Embed:
    """Embed с текущим игроком для отметки присутствия."""
    embed = disnake.Embed(
        title=f"📋 Отметка присутствия — Сессия #{session.session_number}",
        description=(
            f"**Игра:** {game.name}\n"
            f"**Игрок {current_index + 1} из {total}:** {current_name}"
        ),
        color=disnake.Color.blurple(),
    )
    embed.set_footer(text="По истечении времени — все считаются присутствующими")
    return embed


def build_attendance_finished_embed(attending: int, total: int) -> disnake.Embed:
    """Embed после завершения отметки."""
    return disnake.Embed(
        title="✅ Отметка завершена",
        description=f"Присутствует **{attending}** из **{total}** игроков.",
        color=disnake.Color.green(),
    )


def build_attendance_canceled_embed() -> disnake.Embed:
    """Embed если сессия была отменена или инвалидирована во время отметки."""
    return disnake.Embed(
        title="❌ Сессия отменена",
        description="Отметка присутствия прервана.",
        color=disnake.Color.red(),
    )