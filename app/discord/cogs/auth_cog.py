#app/discord/cogs/auth_cog.py
from disnake.ext import commands

class AuthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot