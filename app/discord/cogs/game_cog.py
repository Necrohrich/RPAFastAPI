#app/discord/cogs/game_cog.py
from disnake import ApplicationCommandInteraction, Embed
from disnake.ext import commands

from app.core.config import settings
from app.discord.dependencies import game_system_service_ctx
from app.discord.embeds.build_game_system_embed import build_game_system_embed
from app.discord.embeds.build_game_systems_embed import build_game_systems_embed
from app.discord.policies import require_role
from app.discord.views import PaginationView
from app.domain.policies import PlatformPolicies
from app.dto import CreateGameSystemDTO, UpdateGameSystemDTO


class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="game_system", description="Команды для игровой системы")
    async def game_system(self, inter: ApplicationCommandInteraction): ...

    @game_system.sub_command(name="create", description="Создать игровую систему [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def create(
            self,
            inter: ApplicationCommandInteraction,
            name: str,
            description: str = None
    ) -> None:
        await inter.response.defer(ephemeral=True)

        dto = CreateGameSystemDTO(
            name=name,
            description=description
        )
        async with game_system_service_ctx() as game_system_service:
            await game_system_service.create(dto=dto)
        await inter.send("✅ Игровая система успешно создана", ephemeral=True)

    @game_system.sub_command(name="get_all", description="Показать все игровые системы [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def get_all(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with game_system_service_ctx() as game_system_service:
                result = await game_system_service.get_all(page=page, page_size=settings.DISCORD_PAGE_SIZE)
            return build_game_systems_embed(result, page), result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @game_system.sub_command(name="get_by_id", description="Показать игровую систему [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def get_by_id(self, inter: ApplicationCommandInteraction, game_system_id: str) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_system_service_ctx() as game_system_service:
            result = await game_system_service.get_by_id(game_system_id)
        embed = build_game_system_embed(result)
        await inter.send(embed=embed, ephemeral=True)

    @game_system.sub_command(name="update", description="Обновить игровую систему [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def update(
            self,
            inter: ApplicationCommandInteraction,
            game_system_id: str,
            name: str,
            description: str = None
    ) -> None:
        await inter.response.defer(ephemeral=True)

        dto = UpdateGameSystemDTO(
            name=name,
            description=description
        )
        async with game_system_service_ctx() as game_system_service:
            await game_system_service.update(game_system_id=game_system_id, dto=dto)
        await inter.send("✅ Игровая система успешно обновлена", ephemeral=True)

    @game_system.sub_command(name="delete", description="Удалить игровую систему [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def delete(
            self,
            inter: ApplicationCommandInteraction,
            game_system_id: str
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_system_service_ctx() as game_system_service:
            await game_system_service.delete(game_system_id)
        await inter.send("✅ Игровая система удалена", ephemeral=True)