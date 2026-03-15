# app/discord/views/game_page_view.py
from uuid import UUID
from disnake import MessageInteraction, ButtonStyle, Embed
from disnake.ui import Button, button

from app.core.config import settings
from app.discord.dependencies import game_service_ctx, user_service_ctx, character_service_ctx
from app.discord.embeds.build_game_characters_embed import build_game_characters_embed
from app.discord.embeds.build_game_players_embed import build_game_players_embed
from app.discord.views.pagination_view import PaginationView
from app.discord.views.base_view import BaseView
from app.discord.views.select_view import SelectView
from app.domain.enums import PlayerStatusEnum


class GamePageView(BaseView):
    def __init__(self, game_id: UUID = None):
        super().__init__(timeout=180)
        self.game_id = game_id

    @button(label="👥 Players", style=ButtonStyle.secondary, custom_id="game_page:players", row=0)
    async def players_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with game_service_ctx() as game_service:
                result = await game_service.get_players(
                    self.game_id, page=page, page_size=settings.DISCORD_PAGE_SIZE, status=PlayerStatusEnum.ACCEPTED
                )
            result_embed = build_game_players_embed(result, page)
            return result_embed, result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages, start_page=1)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="➕ Character", style=ButtonStyle.success, custom_id="game_page:attach_character", row=0)
    async def attach_character_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            characters = await user_service.get_my_characters_list(user.id)

        async def on_character_selected(cb_inter: MessageInteraction, character_id: str):
            async with game_service_ctx() as game_service:
                await game_service.attach_character(self.game_id, UUID(character_id), user.id)
            await cb_inter.followup.send("✅ Персонаж добавлен в игру", ephemeral=True)

        view = SelectView(
            items=characters,
            display_field="name",
            title="Мои персонажи",
            callback=on_character_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите персонажа:", view=view, ephemeral=True)

    @button(label="👥 Player's characters", style=ButtonStyle.secondary, custom_id="game_page:player_characters",
            row=0)
    async def player_characters_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with character_service_ctx() as character_service:
                result = await character_service.get_players_characters_by_game_id(self.game_id, page=page,
                                                                page_size=settings.DISCORD_PAGE_SIZE)
            result_embed = build_game_characters_embed(result, page, title="👥 Персонажи игроков")
            return result_embed, result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages, start_page=1)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    # @button(label="👑 GM's characters", style=ButtonStyle.secondary, custom_id="game_page:gm_characters", row=0)
    # async def gm_characters_button(self, _: Button, inter: MessageInteraction) -> None:
    #     await inter.response.defer(ephemeral=True)
    #
    #     async def fetch_page(page: int) -> tuple[Embed, int]:
    #         async with character_service_ctx() as character_service:
    #             result = await character_service.get_gm_characters_by_game_id(
    #                 self.game_id, page=page, page_size=5
    #             )
    #         result_embed = build_game_characters_embed(result, page, title="👑 Персонажи мастера")
    #         return result_embed, result.total_pages
    #
    #     embed, total_pages = await fetch_page(1)
    #     view = PaginationView(fetch_page=fetch_page, total_pages=total_pages, start_page=1)
    #     await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="❌ Detach character", style=ButtonStyle.danger, custom_id="game_page:detach_character", row=1)
    async def detach_character_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with character_service_ctx() as character_service:
            result = await character_service.get_list_by_game_id_and_user_id(self.game_id, user.id)

        if not result:
            await inter.followup.send("📭 Персонажей нет", ephemeral=True)
            return

        async def on_character_selected(cb_inter: MessageInteraction, character_id: str):
            async with game_service_ctx() as game_service:
                await game_service.detach_character(self.game_id, UUID(character_id), user.id)
            await cb_inter.followup.send("✅ Персонаж удалён из игры", ephemeral=True)

        view = SelectView(
            items=result,
            display_field="name",
            title="Персонажи",
            callback=on_character_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите персонажа:", view=view, ephemeral=True)

    @button(label="🚫 Leave game", style=ButtonStyle.danger, custom_id="game_page:leave_game", row=1)
    async def leave_game_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with game_service_ctx() as game_service:
            await game_service.remove_player(self.game_id, user.id, user.id)

        await inter.followup.send("✅ Вы покинули игру", ephemeral=True)
