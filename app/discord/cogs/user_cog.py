#app/discord/cogs/user_cog.py
from disnake.ext import commands

class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot