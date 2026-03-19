# app/discord/modals/reviews/review_npc_modal.py
import disnake
from disnake.ui import TextInput

from app.discord.modals.base_modal import BaseModal


class ReviewNpcModal(BaseModal):
    """
    Модалка для добавления НИП к отзыву.

    Пользователь вводит имена через запятую.
    При повторном открытии показывает уже сохранённые значения для дополнения.
    После подтверждения вызывает callback(inter, list[str]).
    """

    def __init__(self, current_npc: list[str] | None = None, callback=None):
        self._cb = callback
        current_value = ", ".join(current_npc) if current_npc else ""
        components = [
            TextInput(
                label="Имена НИП через запятую",
                custom_id="npc_input",
                style=disnake.TextInputStyle.long,
                placeholder="Например: Барон фон Кранц, Таверна хозяйка Мarta",
                min_length=1,
                max_length=500,
                required=True,
                value=current_value,
            ),
        ]
        super().__init__(
            title="Запомнившиеся НИП",
            custom_id="modal:review_npc",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        raw = inter.text_values["npc_input"]

        # Проверяем формат — хотя бы одно непустое имя
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if not names:
            await inter.followup.send(
                "❌ Неверный формат. Введите имена НИП через запятую.",
                ephemeral=True,
            )
            return

        if self._cb:
            await self._cb(inter, names)
        else:
            await inter.followup.send("✅ НИП сохранены.", ephemeral=True)