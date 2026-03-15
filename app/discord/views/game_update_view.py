#app/discord/views/game_update_view.py
from uuid import UUID

from disnake import MessageInteraction

from app.discord.dependencies import game_system_service_ctx, user_service_ctx
from app.discord.modals.game_update_modal import GameUpdateModal
from app.discord.views.base_view import BaseView
from app.discord.views.select_view import SelectView
from app.discord.wizards import GameUpdateState


class GameUpdateView(BaseView):
    """Пошаговый wizard обновления игры."""

    def __init__(self, state: GameUpdateState = None):
        super().__init__(timeout=180)
        self.state = state or GameUpdateState()

    async def start(self, inter: MessageInteraction):
        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            games = await user_service.get_my_games_list(user.id)

        async with game_system_service_ctx() as game_system_service:
            game_systems = await game_system_service.get_all_list()

        self.state.game_systems = game_systems  # кэшируем в state

        view = SelectView(
            items=games,
            display_field="name",
            title="Мои игры",
            callback=self._on_game_selected,
            skippable=False,
            modal_callback=False,
        )
        await inter.followup.send("Шаг 1: Выберите игру", view=view, ephemeral=True)

    async def _on_game_selected(self, cb_inter: MessageInteraction, game_id: UUID):
        self.state.game_id = game_id
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
        await cb_inter.response.send_modal(GameUpdateModal(self.state))