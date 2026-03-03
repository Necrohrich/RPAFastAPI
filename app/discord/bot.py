#app/discord/bot.py

import disnake
from disnake.ext import commands

from app.discord.loader import load_cogs

class RPABot(commands.InteractionBot):
    def __init__(self):
        intents = disnake.Intents.all()

        super().__init__(intents=intents)

    async def setup_hook(self):
        await load_cogs(self)