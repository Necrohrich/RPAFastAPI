# app/discord/embeds/build_my_games_embed.py
from disnake import Embed, Color
from app.dto import PaginatedResponseDTO, GameResponseDTO


def build_my_games_embed(result: PaginatedResponseDTO[GameResponseDTO], page: int) -> Embed:
    embed = Embed(title="🎲 Мои игры", color=Color.blue())

    if not result.items:
        embed.description = "У вас пока нет созданных игр."
    else:
        for game in result.items:
            value_lines = [f"🆔 `{game.id}`\n\u200b"]
            if game.gm_id:
                value_lines.append(f"👤 GM: <@{game.gm_id}>\n\u200b")
            if game.discord_role_id:
                value_lines.append(f"🎭 Роль: <@&{game.discord_role_id}>\n\u200b")
            if game.discord_main_channel_id:
                value_lines.append(f"📢 Канал: <#{game.discord_main_channel_id}>\n\u200b")

            embed.add_field(
                name=f"**{game.name}**",
                value="\n".join(value_lines),
                inline=False,
            )

    embed.set_footer(text=f"Страница {page} / {result.total_pages} | Всего: {result.total}")
    return embed