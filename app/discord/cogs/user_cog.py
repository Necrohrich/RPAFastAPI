#app/discord/cogs/user_cog.py
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from app.discord.embeds.build_profile_embed import build_profile_embed
from app.discord.policies import discord_policy
from app.discord.views import ProfileView


class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="me", description="Показать мой профиль")
    @discord_policy()
    async def me(self, inter: ApplicationCommandInteraction) -> None:
        embed = build_profile_embed(inter.user_data)  # noqa
        await inter.author.send(embed=embed, view=ProfileView())
        await inter.send("✅ Профиль отправлен в личные сообщения", ephemeral=True)