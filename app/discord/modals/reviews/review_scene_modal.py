# app/discord/modals/reviews/review_scene_modal.py
import disnake
from disnake.ui import TextInput

from app.discord.modals.base_modal import BaseModal


class ReviewSceneModal(BaseModal):
    """
    Модалка для добавления новой сцены к отзыву.

    После подтверждения вызывает callback(inter, scene_name).
    callback получает ModalInteraction уже с выполненным defer.
    """

    def __init__(self, callback=None):
        self._cb = callback
        components = [
            TextInput(
                label="Название сцены",
                custom_id="scene_name_input",
                style=disnake.TextInputStyle.short,
                placeholder="Например: Финальная битва с боссом",
                min_length=1,
                max_length=100,
                required=True,
            ),
        ]
        super().__init__(
            title="Добавить лучшую сцену",
            custom_id="modal:review_scene",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        # Defer ПЕРВЫМ — до любой async-работы, иначе токен протухнет за 3 сек.
        await inter.response.defer(ephemeral=True)
        scene_name = inter.text_values["scene_name_input"].strip()
        if self._cb:
            await self._cb(inter, scene_name)
        else:
            await inter.followup.send("✅ Сцена записана.", ephemeral=True)