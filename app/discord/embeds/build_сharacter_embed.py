#app/discord/embeds/build_character_embed.py
import os
from disnake import Embed, Color, File
from app.utils.files import get_base_dir

IMAGE_PATH = os.path.join(get_base_dir(), "images", "character_system_wallpaper.png")

def build_character_embed() -> tuple[Embed, File]:
    file = File(IMAGE_PATH, filename="character_system_wallpaper.png")

    embed = Embed(title="Character Menu", color=Color.from_rgb(1, 121, 111))
    embed.description = (
        "Добро пожаловать в систему создания персонажа платформы RolePlayAsylum.\n"
        "- Используйте Create для создания нового персонажа.\n"
        "- Используйте Update для обновления данных персонажа.\n"
        "- Используйте Delete для удаления персонажа.\n"
    )
    embed.set_image(url="attachment://character_system_wallpaper.png")

    return embed, file
