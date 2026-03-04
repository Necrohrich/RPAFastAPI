#app/discord/modals/register_modal.py
from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import auth_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.dto.auth_dtos import RegisterRequestDTO


class RegisterModal(BaseModal):

    def __init__(self):
        components = [
            TextInput(
                label="Введите login",
                custom_id="login_input",
                style=TextInputStyle.short,
                min_length=3,
                max_length=30,
            ),
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
            TextInput(
                label="Повторите пароль",
                custom_id="confirm_password",
                style=TextInputStyle.short,
                min_length=8,
                max_length=128,
            ),
        ]
        super().__init__(
            title="Register Window",
            custom_id="modal:register",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        password = inter.text_values["password_input"]
        confirm = inter.text_values["confirm_password"]

        if password != confirm:
            await inter.followup.send("❌ Пароли не совпадают.", ephemeral=True)
            return

        dto = RegisterRequestDTO(
            login=inter.text_values["login_input"],
            email=inter.text_values["email_input"],
            password=password,
            discord_id=inter.author.id
        )

        async with auth_service_ctx() as auth_service:
            await auth_service.register(dto)

        await inter.followup.send("✅ Регистрация прошла успешно", ephemeral=True)
