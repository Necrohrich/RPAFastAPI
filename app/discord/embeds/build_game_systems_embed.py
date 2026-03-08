#app/discord/embeds/build_game_systems_embed.py
from disnake import Embed, Color
from app.dto import PaginatedResponseDTO, GameSystemResponseDTO

def build_game_systems_embed(result: PaginatedResponseDTO[GameSystemResponseDTO], page: int) -> Embed:
    embed = Embed(title="⚙️ Игровые системы", color=Color.blue())

    if not result.items:
        embed.description = "Игровые системы не найдены."
    else:
        for system in result.items:
            value_lines = [f"🆔 `{system.id}`\n\u200b"]
            if system.description:
                value_lines.append(system.description)

            embed.add_field(
                name=f"**{system.name}**\n\u200b",
                value="\n".join(value_lines),
                inline=False,
            )

    embed.set_footer(text=f"Страница {page} / {result.total_pages} | Всего: {result.total}")
    return embed