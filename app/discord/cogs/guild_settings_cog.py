# app/discord/cogs/guild_settings_cog.py
import disnake
from disnake.ext import commands

from app.discord.dependencies import guild_settings_service_ctx
from app.discord.policies import require_role
from app.domain.policies import PlatformPolicies


class GuildSettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="guild", description="Команды для настройки сервера")
    async def guild(self, inter: disnake.ApplicationCommandInteraction) -> None: ...

    @guild.sub_command(name="set_role_anchor", description="Установить якорь позиции ролей [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def set_role_anchor(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role = commands.Param(description="Роль-якорь для позиционирования временных ролей"),
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with guild_settings_service_ctx() as settings_service:
            await settings_service.set_role_anchor(inter.guild_id, role.id)

        await inter.followup.send(
            f"✅ Якорь ролей установлен: {role.mention}", ephemeral=True
        )

    @guild.sub_command(name="clear_role_anchor", description="Сбросить якорь позиции ролей [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def clear_role_anchor(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with guild_settings_service_ctx() as settings_service:
            await settings_service.set_role_anchor(inter.guild_id, None)

        await inter.followup.send("✅ Якорь ролей сброшен", ephemeral=True)

    @guild.sub_command(name="get_settings", description="Показать настройки сервера [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def get_settings(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with guild_settings_service_ctx() as settings_service:
            settings = await settings_service.get(inter.guild_id)

        anchor = f"<@&{settings.role_position_anchor_id}>" if settings.role_position_anchor_id else "Не задан"
        embed = disnake.Embed(title="⚙️ Настройки сервера", color=disnake.Color.blue())
        embed.add_field(name="🎭 Якорь ролей", value=anchor, inline=False)
        await inter.followup.send(embed=embed, ephemeral=True)