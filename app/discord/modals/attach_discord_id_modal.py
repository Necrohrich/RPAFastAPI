#app/discord/modals/attach_discord_id_modal.py
from app.discord.dependencies import user_service_ctx
from app.discord.modals.base_modal import BaseModal
from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

class AttachDiscordIdModal(BaseModal):
    def __init__(self):
        components = [
            TextInput(
                label="Введите дополнительный discord_id",
                custom_id="discord_id_input",
                style=TextInputStyle.short,
                min_length=17,
                max_length=18,
            ),
        ]
        super().__init__(
            title="Attach Discord Id Window",
            custom_id="modal:attach_discord_id",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        discord_id_input = inter.text_values["discord_id_input"]

        if not discord_id_input.isdigit():
            await inter.followup.send("❌ Discord ID должен содержать только цифры", ephemeral=True)
            return

        discord_id_input = int(discord_id_input)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

            await user_service.attach_secondary_discord_id(user.id, discord_id_input)

        await inter.followup.send("✅ Discord ID успешно привязан", ephemeral=True)