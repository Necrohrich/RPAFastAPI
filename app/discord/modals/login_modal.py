# app/discord/modals/login_modal.py
from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import auth_service_ctx, user_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.discord.utils.interaction_utils import get_device_info
from app.dto.auth_dtos import LoginRequestDTO


class LoginModal(BaseModal):

    def __init__(self):
        components = [
            TextInput(
                label="Введите email",
                custom_id="email_input",
                style=TextInputStyle.short,
                min_length=6,
                max_length=255,
            ),
            TextInput(
                label="Введите пароль",
                custom_id="password_input",
                style=TextInputStyle.short,
                min_length=8,
                max_length=128,
            ),
        ]
        super().__init__(
            title="Login Window",
            custom_id="modal:login",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        dto = LoginRequestDTO(
            email=inter.text_values["email_input"],
            password=inter.text_values["password_input"],
            device_info=get_device_info(inter),
        )

        async with auth_service_ctx() as auth_service:
            auth_response, current_user = await auth_service.login_and_get_user(dto)

        async with user_service_ctx() as user_service:
            if current_user.primary_discord_id is None:
                await user_service.attach_primary_discord_id(
                    user_id=current_user.id,
                    discord_id=inter.author.id,
                )
            elif (
                    current_user.primary_discord_id != inter.author.id
                    and current_user.secondary_discord_id is None
            ):
                await user_service.attach_secondary_discord_id(
                    user_id=current_user.id,
                    discord_id=inter.author.id,
                )

        await inter.followup.send("✅ Вход в систему прошел успешно", ephemeral=True)
