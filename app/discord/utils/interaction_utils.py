# app/discord/utils/interaction_utils.py
from disnake import Interaction

def get_device_info(inter: Interaction) -> str:
    locale = str(inter.locale) if inter.locale else "unknown"
    guild_id = str(inter.guild_id) if inter.guild_id else "DM"

    return f"discord:{inter.author.id}:guild={guild_id}:locale={locale}"