#app/discord/cogs/user_cog.py
from disnake import ApplicationCommandInteraction, User
from disnake.ext import commands

from app.discord.dependencies import user_service_ctx
from app.discord.embeds.build_profile_embed import build_profile_embed
from app.discord.policies import discord_policy, require_role
from app.discord.views import ProfileView
from app.domain.enums import PlatformRoleEnum
from app.domain.policies import PlatformPolicies


class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="me", description="Показать мой профиль")
    @discord_policy()
    async def me(self, inter: ApplicationCommandInteraction) -> None:
        embed = build_profile_embed(inter.user_data)  # noqa
        await inter.author.send(embed=embed, view=ProfileView())
        await inter.send("✅ Профиль отправлен в личные сообщения", ephemeral=True)

    @commands.slash_command(name="user", description="Команды для пользователей")
    async def user(self, inter: ApplicationCommandInteraction): ...

    @user.sub_command(name="update_role", description="Обновить роль пользователя [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def update_role(
            self,
            inter: ApplicationCommandInteraction,
            user: User,
            role: PlatformRoleEnum = None) -> None:

        async with user_service_ctx() as user_service:
            dto = await user_service.get_user_by_discord(user.id)
            await user_service.update_role(dto.id, role)

        await inter.send(f"✅ Роль пользователя успешно изменена на {role}", ephemeral=True)

    @user.sub_command(name="view", description="Увидеть профиль пользователя [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def view(
            self,
            inter: ApplicationCommandInteraction,
            user: User) -> None:
        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(user.id)

        embed = build_profile_embed(user)  # noqa
        await inter.send(embed=embed, ephemeral=True)
