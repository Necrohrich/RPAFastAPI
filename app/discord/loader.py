#app/discord/loader.py
import logging

from app.discord.cogs import AuthCog, UserCog, CharacterCog, GameCog
from app.discord.views import AuthView, ProfileView

logger = logging.getLogger(__name__)

def load_cogs(bot):
    bot.add_cog(AuthCog(bot))
    bot.add_cog(UserCog(bot))
    bot.add_cog(CharacterCog(bot))
    bot.add_cog(GameCog(bot))

def register_views(bot):
    logger.debug("Persistent views registered")
    bot.add_view(AuthView())
    bot.add_view(ProfileView())