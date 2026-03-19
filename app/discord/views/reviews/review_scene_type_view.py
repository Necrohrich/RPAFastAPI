# app/discord/views/reviews/review_scene_type_view.py
"""
View для выбора типа игровой сцены.

Шаг 1 — пользователь вводит название сцены в ReviewSceneModal.
Шаг 2 — этот view предлагает выбрать тип сцены через StringSelect.
После выбора вызывает callback(inter, scene_name, scene_type).
"""
from __future__ import annotations

import disnake
from disnake.ui import StringSelect

from app.discord.views.base_view import BaseView
from app.domain.enums.review_scene_type_enum import ReviewSceneTypeEnum

_SCENE_OPTIONS = [
    disnake.SelectOption(label="🎭 Комедия",   value=ReviewSceneTypeEnum.COMEDY,  description="Смешная или забавная сцена"),
    disnake.SelectOption(label="👻 Хоррор",    value=ReviewSceneTypeEnum.HORROR,  description="Страшная или мрачная сцена"),
    disnake.SelectOption(label="⚔️ Экшен",     value=ReviewSceneTypeEnum.ACTION,  description="Боевая или динамичная сцена"),
    disnake.SelectOption(label="🎭 Драма",     value=ReviewSceneTypeEnum.DRAMA,   description="Эмоциональная или драматичная сцена"),
    disnake.SelectOption(label="💕 Романтика", value=ReviewSceneTypeEnum.ROMANCE, description="Романтическая сцена"),
]


class ReviewSceneTypeView(BaseView):
    """
    View для выбора типа сцены после ввода её названия.

    После выбора вызывает callback(inter, scene_name, scene_type_value).
    """

    def __init__(self, scene_name: str, callback):
        super().__init__(timeout=120)
        self._scene_name = scene_name
        self._cb = callback

        sel = StringSelect(
            placeholder="Выберите тип сцены...",
            options=_SCENE_OPTIONS,
            custom_id="review_scene_type:select",
            row=0,
        )
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        scene_type = inter.values[0]
        await self._cb(inter, self._scene_name, scene_type)