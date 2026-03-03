#app/discord/loader.py

async def load_cogs(bot):
    from app.discord.cogs.auth_cog import AuthCog
    from app.discord.cogs.user_cog import UserCog

    await bot.add_cog(AuthCog(bot))
    await bot.add_cog(UserCog(bot))