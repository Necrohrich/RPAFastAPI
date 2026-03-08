# app/discord/modals/select_search_modal.py
import disnake
from disnake.ui import Modal, TextInput

class SelectSearchModal(Modal):
    def __init__(self, view, origin_inter: disnake.MessageInteraction):
        self._view = view
        self._origin_inter = origin_inter
        components = [TextInput(
            label="Введите запрос",
            custom_id="query",
            placeholder="Например: D&D",
            required=False,
        )]
        super().__init__(
            title="Search",
            custom_id="select_view:search_modal",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        self._view.search = inter.text_values.get("query", "") or ""
        self._view.page = 0
        self._view.rebuild()
        await inter.response.edit_message(view=self._view)