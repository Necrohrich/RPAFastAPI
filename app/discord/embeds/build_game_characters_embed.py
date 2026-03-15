# app/discord/embeds/build_game_characters_embed.py
from disnake import Embed, Color
from app.dto import PaginatedResponseDTO, CharacterResponseDTO

def build_game_characters_embed(
        result: PaginatedResponseDTO[CharacterResponseDTO],
        page: int,
        title: str
) -> Embed:
    embed = Embed(title=title, color=Color.from_rgb(1, 121, 111))

    if not result.items:
        embed.description = "📭 Персонажей нет."
    else:
        for character in result.items:
            value_lines = [f"🆔 `{character.id}`\n\u200b"]
            if character.game_system_name:
                value_lines.append(f"⚙️ Система: {character.game_system_name}\n\u200b")
            if character.avatar:
                value_lines.append(f"🖼️ Аватар: {character.avatar}\n\u200b")
            embed.add_field(
                name=f"**{character.name}**",
                value="\n".join(value_lines),
                inline=False,
            )

    embed.set_footer(text=f"Страница {page} / {result.total_pages} | Всего: {result.total}")
    return embed