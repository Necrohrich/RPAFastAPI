# app/discord/embeds/build_my_characters_embed.py
from disnake import Embed, Color
from app.dto import PaginatedResponseDTO, CharacterResponseDTO

def build_my_characters_embed(result: PaginatedResponseDTO[CharacterResponseDTO], page: int) -> Embed:
    embed = Embed(title="🧙 Мои персонажи", color=Color.purple())

    if not result.items:
        embed.description = "У вас пока нет персонажей."
    else:
        for character in result.items:
            value_lines = [f"🆔 `{character.id}`\n\u200b"]
            if character.game_system_name:
                value_lines.append(f"⚙️ Система: {character.game_system_name} \n\u200b")
            if character.game_name:
                value_lines.append(f"🎲 Игра: {character.game_name} \n\u200b")

            embed.add_field(
                name=f"**{character.name}**",
                value="\n".join(value_lines),
                inline=False,
            )

    embed.set_footer(text=f"Страница {page} / {result.total_pages} | Всего: {result.total}")
    return embed