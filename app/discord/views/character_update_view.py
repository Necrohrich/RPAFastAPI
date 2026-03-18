#app/discord/views/character_update_view.py
from uuid import UUID

from disnake import MessageInteraction

from app.discord.dependencies import game_system_service_ctx, user_service_ctx, character_service_ctx
from app.discord.modals import CharacterUpdateModal
from app.discord.views.base_view import BaseView
from app.discord.views.select_view import SelectView
from app.discord.states.wizards import CharacterUpdateState

class CharacterUpdateView(BaseView):
    """Пошаговый wizard обновления персонажа."""

    def __init__(self, state: CharacterUpdateState = None):
        super().__init__(timeout=180)
        self.state = state or CharacterUpdateState()

    async def start(self, inter: MessageInteraction):
        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            characters = await user_service.get_my_characters_list(user.id)

        async with game_system_service_ctx() as game_system_service:
            game_systems = await game_system_service.get_all_list()

        self.state.game_systems = game_systems  # кэшируем в states

        view = SelectView(
            items=characters,
            display_field="name",
            title="Персонажи",
            callback=self._on_character_selected,
            skippable=False,
            modal_callback=False,
        )
        await inter.followup.send("Шаг 1: Выберите персонажа", view=view, ephemeral=True)

    async def _on_character_selected(self, cb_inter: MessageInteraction, character_id: UUID):
        self.state.character_id = character_id
        async with character_service_ctx() as character_service:
            self.state.current_character = await character_service.get_by_id(character_id)
        await self._step_select_game_system(cb_inter)

    async def _step_select_game_system(self, inter: MessageInteraction):
        view = SelectView(
            items=self.state.game_systems,
            display_field="name",
            title="Игровая система",
            callback=self._on_game_system_selected,
            skippable=True,
            modal_callback=True,
        )
        await inter.followup.send("Шаг 2: Выберите игровую систему", view=view, ephemeral=True)

    async def _on_game_system_selected(self, cb_inter: MessageInteraction, game_system_id: UUID | None):
        self.state.game_system_id = game_system_id
        await cb_inter.response.send_modal(CharacterUpdateModal(self.state))