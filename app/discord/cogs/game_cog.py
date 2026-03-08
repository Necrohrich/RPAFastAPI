#app/discord/cogs/game_cog.py
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot