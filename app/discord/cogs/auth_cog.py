#app/discord/cogs/auth_cog.py
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from app.discord.embeds.build_auth_embed import build_auth_embed
from app.discord.policies import require_role
from app.discord.views import AuthView
from app.domain.policies import PlatformPolicies


class AuthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="auth", description="Показать систему Аутентификации [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def auth_menu(
            self,
            inter: ApplicationCommandInteraction,
    ) -> None:
        embed, file = build_auth_embed()

        await inter.send(embed=embed, file=file, view=AuthView())