# app/discord/views/pagination_view.py
from typing import Callable, Awaitable

from disnake import MessageInteraction, ButtonStyle, Embed
from disnake.ui import button, Button
from app.discord.views.base_view import BaseView

class PaginationView(BaseView):
    def __init__(
        self,
            fetch_page: Callable[[int], Awaitable[tuple[Embed, int]]], # fetch_page(page) -> (embed, total_pages)
            total_pages: int,
            start_page: int = 1,
    ) -> None:
        super().__init__(timeout=180)
        self.fetch_page = fetch_page
        self.current_page = start_page
        self.total_pages = total_pages
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.current_page <= 1
        self.next_button.disabled = self.current_page >= self.total_pages

    @button(label="◀", style=ButtonStyle.secondary, custom_id="pagination:prev")
    async def prev_button(self, _: Button, inter: MessageInteraction):
        await inter.response.defer()
        self.current_page -= 1
        embed, self.total_pages = await self.fetch_page(self.current_page)
        self._update_buttons()
        await inter.edit_original_response(embed=embed, view=self)

    @button(label="▶", style=ButtonStyle.secondary, custom_id="pagination:next")
    async def next_button(self, _: Button, inter: MessageInteraction):
        await inter.response.defer()
        self.current_page += 1
        embed, self.total_pages = await self.fetch_page(self.current_page)
        self._update_buttons()
        await inter.edit_original_response(embed=embed, view=self)

    @button(label="Close", style=ButtonStyle.danger, custom_id="pagination:close")
    async def close_button(self, _: Button, inter: MessageInteraction):
        await inter.response.defer()
        await inter.delete_original_response()