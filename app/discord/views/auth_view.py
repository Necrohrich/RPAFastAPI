# app/discord/views/auth_view.py
from disnake import ButtonStyle, MessageInteraction
from disnake.ui import button, Button

from app.discord.modals.login_modal import LoginModal
from app.discord.modals.register_modal import RegisterModal
from app.discord.views.base_view import BaseView


class AuthView(BaseView):
    """
    Вьюшка для Аутентификации через дискорд
    """

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Login", style=ButtonStyle.primary, custom_id="auth:login", row=0)
    async def login_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(LoginModal())

    @button(label="Register", style=ButtonStyle.primary, custom_id="auth:register", row=0)
    async def register_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(RegisterModal())

