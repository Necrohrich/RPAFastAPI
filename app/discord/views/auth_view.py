# app/discord/views/auth_view.py
from disnake import ButtonStyle, MessageInteraction
from disnake.ui import button, Button

from app.discord.dependencies import user_service_ctx
from app.discord.embeds.build_profile_embed import build_profile_embed
from app.discord.modals.login_modal import LoginModal
from app.discord.modals.register_modal import RegisterModal
from app.discord.views import ProfileView
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

    @button(label="Me", style=ButtonStyle.primary, custom_id="auth:me", row=0)
    async def me_button(self, _: Button, inter: MessageInteraction) -> None:
        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
        
        embed = build_profile_embed(user)
        await inter.author.send(embed=embed, view=ProfileView())
        await inter.send("✅ Профиль отправлен в личные сообщения", ephemeral=True)

