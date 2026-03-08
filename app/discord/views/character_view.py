#app/discord/views/character_view.py
from uuid import UUID

from disnake import ButtonStyle, MessageInteraction
from disnake.ui import button, Button

from app.discord.dependencies import game_system_service_ctx
from app.discord.modals import CharacterCreateModal
from app.discord.views.select_view import SelectView
from app.discord.views.base_view import BaseView

class CharacterView(BaseView):
    """
    Вьюшка для работы с персонажем
    """

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Create", style=ButtonStyle.primary, custom_id="character:create", row=0)
    async def create_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_system_service_ctx() as gs_service:
            game_systems = await gs_service.get_all_list()

        async def on_game_system_selected(cb_inter: MessageInteraction, game_system_id: UUID):
            await cb_inter.response.send_modal(CharacterCreateModal(game_system_id))

        view = SelectView(
            items=game_systems,
            display_field="name",
            title="Игровая система",
            callback=on_game_system_selected,
            skippable=True,
        )
        await inter.followup.send("Выберите игровую систему:", view=view, ephemeral=True)

    @button(label="Update", style=ButtonStyle.primary, custom_id="character:update", row=0)
    async def update_button(self, _: Button, inter: MessageInteraction) -> None:...

    @button(label="Delete", style=ButtonStyle.danger, custom_id="character:delete", row=0)
    async def delete_button(self, _: Button, inter: MessageInteraction) -> None:...