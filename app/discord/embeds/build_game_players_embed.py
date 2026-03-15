# app/discord/embeds/build_game_players_embed.py
from disnake import Embed, Color
from app.dto import PaginatedResponseDTO, GamePlayerResponseDTO


def build_game_players_embed(result: PaginatedResponseDTO[GamePlayerResponseDTO], page: int) -> Embed:
    embed = Embed(title="👥 Игроки", color=Color.from_rgb(1, 121, 111))

    if not result.items:
        embed.description = "📭 Игроков нет."
    else:
        for player in result.items:
            embed.add_field(
                name=f"**{player.name}**",
                value=f"🆔 `{player.user_id}`",
                inline=False,
            )

    embed.set_footer(text=f"Страница {page} / {result.total_pages} | Всего: {result.total}")
    return embed