# app/discord/views/select_view.py
from typing import Any, Callable, Awaitable

import disnake
from disnake.ui import Button, StringSelect

from app.discord.modals import SelectSearchModal
from app.discord.views.base_view import BaseView

PAGE_SIZE = 25

class SelectView(BaseView):
    """
    Универсальный View для выбора элемента из списка с пагинацией и поиском.

    Отображает StringSelect с опциями текущей страницы, кнопки навигации ◀/▶
    и кнопку поиска, открывающую Modal для фильтрации списка.
    Всегда возвращает str(item.id) выбранного элемента в callback.

    Args:
        items: Список объектов с атрибутами id и display_field.
        display_field: Имя атрибута, отображаемого в селекте (например "name").
        title: Заголовок placeholder селекта.
        callback: Асинхронная функция вида callback(inter, selected_id: str).
        page: Начальная страница (по умолчанию 0).
        search: Начальный поисковый запрос (по умолчанию пустой).
        skippable: Указывает можно ли пропустить селект
    """

    def __init__(
        self,
        items: list[Any],
        display_field: str,
        title: str,
        callback: Callable[[disnake.MessageInteraction, str], Awaitable[None]],
        page: int = 0,
        search: str = "",
        skippable: bool = False
    ):
        super().__init__(timeout=180)
        self.all_items = items
        self.display_field = display_field
        self.title = title
        self._callback = callback
        self.page = page
        self.search = search
        self.skippable = skippable
        self.rebuild()

    # ── helpers ─────────────────────────────────────────────

    @property
    def _filtered(self) -> list[Any]:
        """Возвращает items, отфильтрованные по-текущему search-запросу."""
        if not self.search:
            return self.all_items
        q = self.search.lower()
        return [i for i in self.all_items if q in getattr(i, self.display_field, "").lower()]

    @property
    def _total_pages(self) -> int:
        """Возвращает общее число страниц для текущего отфильтрованного списка."""
        return max(1, (len(self._filtered) + PAGE_SIZE - 1) // PAGE_SIZE)

    def rebuild(self):
        """
        Пересобирает все компоненты View: StringSelect и кнопки навигации.
        Вызывается после изменения page или search.
        """
        self.clear_items()
        filtered = self._filtered
        self.page = max(0, min(self.page, self._total_pages - 1))
        page_items = filtered[self.page * PAGE_SIZE:(self.page + 1) * PAGE_SIZE]

        options = [
            disnake.SelectOption(label=getattr(i, self.display_field)[:100], value=str(i.id))
            for i in page_items
        ] or [disnake.SelectOption(label="Ничего не найдено", value="__empty__")]

        sel = StringSelect(
            placeholder=f"{self.title} — {self.page + 1}/{self._total_pages}",
            options=options,
            custom_id="select_view:select",
            row=0,
        )
        sel.callback = self._on_select
        self.add_item(sel)

        for label, cid, cb, style, disabled, row in [
            ("◀",         "select_view:prev",   self._on_prev,   disnake.ButtonStyle.secondary, self.page == 0,                     1),
            ("🔍 Search", "select_view:search", self._on_search, disnake.ButtonStyle.primary,   False,                              1),
            ("▶",         "select_view:next",   self._on_next,   disnake.ButtonStyle.secondary, self.page >= self._total_pages - 1, 1),
            ("✖ Cancel",  "select_view:cancel", self._on_cancel, disnake.ButtonStyle.danger,    False,                              2),
        ]:
            btn = Button(label=label, style=style, custom_id=cid, disabled=disabled, row=row)
            btn.callback = cb
            self.add_item(btn)

        if self.skippable:
            skip_btn = Button(label="⏭ Skip", style=disnake.ButtonStyle.secondary,
                              custom_id="select_view:skip", row=2)
            skip_btn.callback = self._on_skip
            self.add_item(skip_btn)

    # ── callbacks ────────────────────────────────────────────

    async def _on_select(self, inter: disnake.MessageInteraction):
        """Обрабатывает выбор элемента. Передаёт id выбранного элемента в callback."""
        if (selected := inter.values[0]) == "__empty__":
            await inter.response.defer()
            return
        await self._callback(inter, selected)

    async def _on_prev(self, inter: disnake.MessageInteraction):
        """Переключает на предыдущую страницу и пересобирает View."""
        await inter.response.defer()
        self.page -= 1
        self.rebuild()
        await inter.edit_original_response(view=self)

    async def _on_next(self, inter: disnake.MessageInteraction):
        """Переключает на следующую страницу и пересобирает View."""
        await inter.response.defer()
        self.page += 1
        self.rebuild()
        await inter.edit_original_response(view=self)

    async def _on_search(self, inter: disnake.MessageInteraction):
        """Открывает Modal для ввода поискового запроса."""
        await inter.response.send_modal(SelectSearchModal(self, inter))

    async def _on_skip(self, inter: disnake.MessageInteraction):
        """Пропускает селект"""
        await self._callback(inter, None)  # передаём None

    @staticmethod
    async def _on_cancel(inter: disnake.MessageInteraction):
        """Закрывает View, удаляя сообщение."""
        await inter.response.defer()
        await inter.delete_original_response()