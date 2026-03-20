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

    Дубликаты (без учёта регистра) автоматически удаляются.
    """

    def __init__(self, current_npc: list[str] | None = None, callback=None):
        self._cb = callback

        text_input_kwargs = dict(
            label="Имена НИП через запятую",
            custom_id="npc_input",
            style=disnake.TextInputStyle.long,
            placeholder="Например: Барон фон Кранц, Таверна хозяйка Marta",
            min_length=1,
            max_length=500,
            required=True,
        )
        if current_npc:
            text_input_kwargs["value"] = ", ".join(current_npc)

        components = [TextInput(**text_input_kwargs)]
        super().__init__(
            title="Запомнившиеся НИП",
            custom_id="modal:review_npc",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        raw = inter.text_values["npc_input"]

        # Проверяем формат — хотя бы одно непустое имя
        names_raw = [n.strip() for n in raw.split(",") if n.strip()]
        if not names_raw:
            await inter.followup.send(
                "❌ Неверный формат. Введите имена НИП через запятую.",
                ephemeral=True,
            )
            return

        # Дедупликация без учёта регистра — сохраняем первое вхождение
        seen: set[str] = set()
        names: list[str] = []
        for name in names_raw:
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)

        if self._cb:
            await self._cb(inter, names)
        else:
            await inter.followup.send("✅ НИП сохранены.", ephemeral=True)