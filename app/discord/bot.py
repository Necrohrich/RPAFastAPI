#app/discord/bot.py
import logging

import disnake
from disnake.ext import commands

from app.discord.error_handlers import setup_error_handlers
from app.discord.loader import load_cogs

logger = logging.getLogger(__name__)

class RPABot(commands.InteractionBot):
    def __init__(self):
        intents = disnake.Intents.all()

        super().__init__(intents=intents)

        self._startup_notified: bool = False

    async def setup_hook(self):
        await load_cogs(self)
        setup_error_handlers(self)

    async def on_ready(self):
        # защита от повторных вызовов при реконнекте
        if self._startup_notified:
            return

        self._startup_notified = True

        logger.info("Discord bot is running as %s", self.user)