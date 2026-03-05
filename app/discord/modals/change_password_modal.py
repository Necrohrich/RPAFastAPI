#app/discord/modals/change_password_modal.py
from app.discord.dependencies import user_service_ctx
from app.discord.modals.base_modal import BaseModal
from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.dto.auth_dtos import ChangePasswordDTO


class ChangePasswordModal(BaseModal):
    def __init__(self):
        components = [
            TextInput(
                label="Введите старый пароль",
                custom_id="old_password_input",
                style=TextInputStyle.short,
                min_length=8,
                max_length=128,
            ),
            TextInput(
                label="Введите новый пароль",
                custom_id="new_password_input",
                style=TextInputStyle.short,
                min_length=8,
                max_length=128,
            ),
        ]
        super().__init__(
            title="Change Password Window",
            custom_id="modal:change_password",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

            dto = ChangePasswordDTO(
                old_password=inter.text_values["old_password_input"],
                new_password=inter.text_values["new_password_input"]
            )

            await user_service.change_password(user.id, dto)

        await inter.followup.send("✅ Пароль успешно изменен", ephemeral=True)