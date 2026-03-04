#app/discord/loader.py
import logging

from app.discord.views.auth_view import AuthView

logger = logging.getLogger(__name__)

def load_cogs(bot):
    from app.discord.cogs.auth_cog import AuthCog
    from app.discord.cogs.user_cog import UserCog
    bot.add_cog(AuthCog(bot))
    bot.add_cog(UserCog(bot))

def register_views(bot):
    logger.debug("Persistent views registered")
    bot.add_view(AuthView())