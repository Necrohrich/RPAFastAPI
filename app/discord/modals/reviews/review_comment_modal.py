# app/discord/modals/reviews/review_comment_modal.py
import disnake
from disnake.ui import TextInput

from app.discord.modals.base_modal import BaseModal


class ReviewCommentModal(BaseModal):
    """
    Модалка для ввода комментария к отзыву.

    После подтверждения вызывает callback(inter, comment_text).
    callback — async функция (inter, str) -> None, определённая во view.
    """

    def __init__(self, current_comment: str = "", callback=None):
        self._cb = callback

        text_input_kwargs = dict(
            label="Ваш комментарий",
            custom_id="comment_input",
            style=disnake.TextInputStyle.long,
            placeholder="Напишите ваши впечатления от сессии...",
            min_length=1,
            max_length=1800,
            required=True,
        )
        if current_comment and current_comment.strip():
            text_input_kwargs["value"] = current_comment

        components = [TextInput(**text_input_kwargs)]
        super().__init__(
            title="Комментарий к отзыву",
            custom_id="modal:review_comment",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        comment = inter.text_values["comment_input"].strip()
        if self._cb:
            await self._cb(inter, comment)
        else:
            await inter.followup.send("✅ Комментарий сохранён.", ephemeral=True)