#app/discord/views/game_menu_view.py
from uuid import UUID

from disnake import ButtonStyle, MessageInteraction
from disnake.ui import button, Button

from app.discord.dependencies import game_system_service_ctx, user_service_ctx, game_service_ctx
from app.discord.embeds.build_game_settings_embed import build_game_settings_embed
from app.discord.modals import GameCreateModal
from app.discord.modals.game_invitation_create_modal import GameInvitationCreateModal
from app.discord.views.game_settings_view import GameSettingsView
from app.discord.views.game_update_view import GameUpdateView
from app.discord.views.select_view import SelectView
from app.discord.views.base_view import BaseView

class GameMenuView(BaseView):
    """
    Вьюшка для работы с играми
    """

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Create", style=ButtonStyle.primary, custom_id="game:create", row=0)
    async def create_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_system_service_ctx() as gs_service:
            game_systems = await gs_service.get_all_list()

        async def on_game_system_selected(cb_inter: MessageInteraction, game_system_id: UUID):
            await cb_inter.response.send_modal(GameCreateModal(game_system_id))

        view = SelectView(
            items=game_systems,
            display_field="name",
            title="Игровая система",
            callback=on_game_system_selected,
            skippable=True,
            modal_callback=True
        )
        await inter.followup.send("Выберите игровую систему:", view=view, ephemeral=True)

    @button(label="Update", style=ButtonStyle.primary, custom_id="game:update", row=0)
    async def update_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        wizard = GameUpdateView()
        await wizard.start(inter)

    @button(label="Delete", style=ButtonStyle.danger, custom_id="game:delete", row=0)
    async def delete_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            games = await user_service.get_my_games(user.id)

        async def on_game_selected(cb_inter: MessageInteraction, game_id: UUID):
            async with game_service_ctx() as game_service:
                await game_service.soft_delete(game_id, user.id)

            await cb_inter.followup.send("✅ Игра успешно удалена", ephemeral=True)

        view = SelectView(
            items=games,
            display_field="name",
            title="Мои игры",
            callback=on_game_selected,
            skippable=False
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)

    @button(label="Settings", style=ButtonStyle.primary, custom_id="game:settings", row=1)
    async def settings_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            games = await user_service.get_my_games_list(user.id)

        async def on_game_selected(cb_inter: MessageInteraction, game_id: UUID):
            async with game_service_ctx() as game_service:
                game = await game_service.get_by_id(game_id)

            embed = build_game_settings_embed(game)
            await cb_inter.author.send(embed=embed, view=GameSettingsView(game_id))
            await cb_inter.followup.send("✅ Настройки игры отправлена в личные сообщения", ephemeral=True)

        view = SelectView(
            items=games,
            display_field="name",
            title="Мои игры",
            callback=on_game_selected,
            skippable=False,
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)
    #
    # @button(label="Open game", style=ButtonStyle.danger, custom_id="game:open", row=1)
    # async def open_button(self, _: Button, inter: MessageInteraction) -> None:
    #     await inter.response.defer(ephemeral=True)
    #
    #     async with user_service_ctx() as user_service:
    #         user = await user_service.get_user_by_discord(inter.author.id)
    #         games = await user_service.get_participated_games_list(user.id)
    #
    #     async def on_game_selected(cb_inter: MessageInteraction, game_id: UUID):
    #
    #         async with game_service_ctx() as game_service:
    #             game = await game_service.get_by_id(game_id)
    #
    #         embed, file = build_game_page_embed(game)
    #         await cb_inter.author.send(embed=embed, file=file, view=GamePageView())
    #         await cb_inter.followup.send("✅ Страница игры отправлена в личные сообщения", ephemeral=True)
    #
    #     view = SelectView(
    #         items=games,
    #         display_field="name",
    #         title="Вы игрок в:",
    #         callback=on_game_selected,
    #         skippable=False,
    #     )
    #     await inter.followup.send("Выберите игру:", view=view, ephemeral=True)

    @button(label="Invite", style=ButtonStyle.primary, custom_id="game:invite", row=1)
    async def invite_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            games = await user_service.get_my_games_list(user.id)

        async def on_game_selected(cb_inter: MessageInteraction, game_id: UUID):

            await cb_inter.response.send_modal(GameInvitationCreateModal(game_id))

        view = SelectView(
            items=games,
            display_field="name",
            title="Мои игры",
            callback=on_game_selected,
            skippable=False,
            modal_callback=True
        )
        await inter.followup.send("Выберите игру:", view=view, ephemeral=True)
