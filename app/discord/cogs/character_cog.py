#app/discord/cogs/character_cog.py
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from app.discord.embeds.build_сharacter_embed import build_character_embed
from app.discord.policies import require_role
from app.discord.views import CharacterView
from app.domain.policies import PlatformPolicies

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="character", description="Показать меню создания персонажа [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def character_menu(
            self,
            inter: ApplicationCommandInteraction,
    ) -> None:
        embed, file = build_character_embed()

        await inter.send(embed=embed, file=file, view=CharacterView())

