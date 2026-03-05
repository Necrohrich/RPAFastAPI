#app/discord/views/profile_view.py
from disnake import ButtonStyle, MessageInteraction
from disnake.ui import button, Button

from app.discord.dependencies import user_service_ctx
from app.discord.embeds.build_profile_embed import build_profile_embed
from app.discord.modals.attach_discord_id_modal import AttachDiscordIdModal
from app.discord.modals.attach_email_modal import AttachEmailModal
from app.discord.modals.change_password_modal import ChangePasswordModal
from app.discord.views.base_view import BaseView


class ProfileView(BaseView):
    """
    Вьюшка для просмотра профиля пользователя
    """

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Refresh", style=ButtonStyle.primary, custom_id="profile:refresh", row=0)
    async def refresh_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        await inter.edit_original_response(embed=build_profile_embed(user))

    @button(label="Change Password", style=ButtonStyle.primary, custom_id="profile:change_password", row=0)
    async def change_password_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(ChangePasswordModal())

    @button(label="Attach Second Email", style=ButtonStyle.primary, custom_id="profile:attach_email", row=0)
    async def attach_email_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(AttachEmailModal())

    @button(label="Attach Second Discord Id", style=ButtonStyle.primary, custom_id="profile:attach_discord_id", row=0)
    async def attach_discord_id_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.send_modal(AttachDiscordIdModal())