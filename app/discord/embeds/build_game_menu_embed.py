#app/discord/embeds/build_game_menu_embed.py
import os

from disnake import Embed, Color, File

from app.utils.files import get_base_dir

IMAGE_PATH = os.path.join(get_base_dir(), "images", "game_menu_wallpaper.png")

def build_game_menu_embed() -> tuple[Embed, File]:
    file = File(IMAGE_PATH, filename="game_menu_wallpaper.png")

    embed = Embed(title="Game Menu", color=Color.from_rgb(1, 121, 111))
    embed.description = (
        "Добро пожаловать в игровое меню.\n"
        "Create - создать новую игру\n"
        "Update - обновить данные вашей игры\n"
        "Delete - удалить вашу игру\n"
        "Settings - настройки моей игры\n"
        "Open game - открыть игру, в которой я участвую\n"
        "Invite - отправить приглашение на вашу игру\n"
    )
    embed.set_image(url="attachment://game_menu_wallpaper.png")

    return embed, file