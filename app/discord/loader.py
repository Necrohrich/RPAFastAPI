#app/discord/loader.py
import logging

logger = logging.getLogger(__name__)

async def load_cogs(bot):
    from app.discord.cogs.auth_cog import AuthCog
    from app.discord.cogs.user_cog import UserCog
    await bot.add_cog(AuthCog(bot))
    await bot.add_cog(UserCog(bot))

def register_views(bot):
    logger.debug("Persistent views registered")
    # from app.discord.views.profile_view import ProfileView
    # bot.add_view(ProfileView())