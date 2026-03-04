#app/discord/embeds/build_auth_embed.py
import os

from disnake import Embed, Color, File

from app.utils.files import get_base_dir

IMAGE_PATH = os.path.join(get_base_dir(), "images", "auth_system_wallpaper.png")

def build_auth_embed() -> tuple[Embed, File]:
    file = File(IMAGE_PATH, filename="auth_system_wallpaper.png")

    embed = Embed(title="Authentication Menu", color=Color.from_rgb(1, 121, 111))
    embed.description = (
        "Добро пожаловать в систему Аутентификации платформы RolePlayAsylum. "
        "Войдите в систему или пройдите регистрацию, если у вас еще нет профиля"
    )
    embed.set_image(url="attachment://auth_system_wallpaper.png")

    return embed, file