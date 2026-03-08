#app/discord/embeds/build_game_system_embed.py
from disnake import Embed, Color
from app.dto import GameSystemResponseDTO

def build_game_system_embed(system: GameSystemResponseDTO) -> Embed:
    embed = Embed(title=f"⚙️ {system.name}", color=Color.blue())
    value_lines = [f"🆔 `{system.id}`\n\u200b"]
    if system.description:
        value_lines.append(system.description)
    embed.description = "\n".join(value_lines)
    return embed