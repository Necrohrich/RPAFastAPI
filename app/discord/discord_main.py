#app/discord/discord_main.py
import asyncio

from app.core.logging_config import setup_logging
from app.discord.bot import RPABot
from app.core.config import settings

setup_logging()

async def main():
    while True:
        bot = RPABot()
        try:
            await bot.start(settings.DISCORD_TOKEN)
        except asyncio.CancelledError:
            await bot.close()
            break
        except Exception as e:
            print(f"Bot crashed: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())