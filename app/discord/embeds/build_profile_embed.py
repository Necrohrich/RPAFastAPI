#app/discord/embeds/build_profile_embed.py
from disnake import Embed, Color

def build_profile_embed(user) -> Embed:
    embed = Embed(title="👤 Ваш профиль", color=Color.from_hex("#5B9BD5"))
    embed.add_field(name="Логин", value=user.login, inline=True)
    embed.add_field(name="Email", value=user.primary_email, inline=True)
    embed.add_field(
        name="Дополнительный Email",
        value=user.secondary_email if user.secondary_email else "None",
        inline=True)
    embed.add_field(name="Discord Id", value=user.primary_discord_id, inline=True)
    embed.add_field(
        name="Дополнительный Discord Id",
        value=user.secondary_discord_id if user.secondary_discord_id else "None",
        inline=True)
    embed.add_field(
        name="Роль",
        value=user.platform_role.value if user.platform_role else "User",
        inline=True,
    )
    return embed