#app/discord/cogs/character_cog.py
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

