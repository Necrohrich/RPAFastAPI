#app/discord/modals/attach_email_modal.py
from app.discord.dependencies import user_service_ctx
from app.discord.modals.base_modal import BaseModal
from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

class AttachEmailModal(BaseModal):
    def __init__(self):
        components = [
            TextInput(
                label="Введите дополнительный email",
                custom_id="email_input",
                style=TextInputStyle.short,
                min_length=6,
                max_length=255,
            ),
        ]
        super().__init__(
            title="Attach Email Window",
            custom_id="modal:attach_email",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        email_input = inter.text_values["email_input"]

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

            await user_service.attach_secondary_email(user.id, email_input)

        await inter.followup.send("✅ Email успешно привязан", ephemeral=True)