#app/discord/views/profile_view.py
from disnake import ButtonStyle, MessageInteraction, Embed
from disnake.ui import button, Button

from app.core.config import settings
from app.discord.dependencies import user_service_ctx
from app.discord.embeds.build_my_characters_embed import build_my_characters_embed
from app.discord.embeds.build_my_games_embed import build_my_games_embed
from app.discord.embeds.build_participated_games_embed import build_participated_games_embed
from app.discord.embeds.build_profile_embed import build_profile_embed
from app.discord.modals.attach_discord_id_modal import AttachDiscordIdModal
from app.discord.modals.attach_email_modal import AttachEmailModal
from app.discord.modals.change_password_modal import ChangePasswordModal
from app.discord.views.base_view import BaseView
from app.discord.views.pagination_view import PaginationView

class ProfileView(BaseView):
    """
    Вьюшка для просмотра профиля пользователя
    """

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Refresh", style=ButtonStyle.primary, custom_id="profile:refresh", row=0)
    async def refresh_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        await inter.edit_original_response(embed=build_profile_embed(user))

    @button(label="Change Password", style=ButtonStyle.primary, custom_id="profile:change_password", row=0)
    async def change_password_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(ChangePasswordModal())

    @button(label="Attach Second Email", style=ButtonStyle.primary, custom_id="profile:attach_email", row=0)
    async def attach_email_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(AttachEmailModal())

    @button(label="Attach Second Discord Id", style=ButtonStyle.primary, custom_id="profile:attach_discord_id", row=0)
    async def attach_discord_id_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(AttachDiscordIdModal())

    @button(label="Get My Games", style=ButtonStyle.primary, custom_id="profile:get_my_games", row=1)
    async def get_my_games(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        discord_id = inter.author.id

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with user_service_ctx() as user_service:
                user = await user_service.get_user_by_discord(discord_id)
                result = await user_service.get_my_games(user.id, page=page, page_size=settings.DISCORD_PAGE_SIZE)
            return build_my_games_embed(result, page), result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="Get Participated Games", style=ButtonStyle.primary, custom_id="profile:get_participated_game", row=1)
    async def get_participated_game(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        discord_id = inter.author.id

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with user_service_ctx() as user_service:
                user = await user_service.get_user_by_discord(discord_id)
                result = await user_service.get_participated_games(user.id, page=page, page_size=settings.DISCORD_PAGE_SIZE)
            return build_participated_games_embed(result, page), result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="Get My Characters", style=ButtonStyle.primary, custom_id="profile:get_my_characters", row=1)
    async def get_my_characters(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        discord_id = inter.author.id

        async def fetch_page(page: int) -> tuple[Embed, int]:
            async with user_service_ctx() as user_service:
                user = await user_service.get_user_by_discord(discord_id)
                result = await user_service.get_my_characters(user.id, page=page, page_size=settings.DISCORD_PAGE_SIZE)
            return build_my_characters_embed(result, page), result.total_pages

        embed, total_pages = await fetch_page(1)
        view = PaginationView(fetch_page=fetch_page, total_pages=total_pages)
        await inter.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="Close", style=ButtonStyle.danger, custom_id="profile:close", row=1)
    async def close_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer()
        await inter.delete_original_response()