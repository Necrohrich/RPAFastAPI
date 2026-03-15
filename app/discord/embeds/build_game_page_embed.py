# app/discord/embeds/build_game_page_embed.py
from disnake import Embed, Color

def build_game_page_embed(game) -> Embed:
    embed = Embed(title=f"⚙️ Настройки игры: {game.name}", color=Color.from_rgb(1, 121, 111))

    embed.description = "Меню доступно в течении 180 секунд или до перезагрузки бота \n"

    embed.add_field(name="🎲 Игровая система", value=game.game_system_name, inline=True)
    embed.add_field(name="👑 Мастер", value=f"<@{game.gm_id}>" if game.gm_id else "Не назначен", inline=True)
    embed.add_field(name="🎭 Роль", value=f"<@&{game.discord_role_id}>" if game.discord_role_id else "Не назначена",
                    inline=True)
    embed.add_field(name="📢 Основной канал", value=f"<#{game.discord_main_channel_id}>"
    if game.discord_main_channel_id else "Не назначен", inline=True)

    return embed