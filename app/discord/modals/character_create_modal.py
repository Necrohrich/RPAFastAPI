#app/discord/modals/character_create_modal.py
from uuid import UUID

from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import character_service_ctx, user_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.dto import CreateCharacterDTO


class CharacterCreateModal(BaseModal):
    def __init__(self, game_system_id: UUID):
        self.game_system_id=game_system_id
        components = [
            TextInput(
                label="Введите имя",
                custom_id="name_input",
                style=TextInputStyle.short,
                min_length=1,
                max_length=255,
            ),
            TextInput(
                label="Введите url аватара",
                custom_id="avatar_url_input",
                style=TextInputStyle.short,
                min_length=10,
                max_length=255,
                required=False
            ),
        ]
        super().__init__(
            title="Character Create Window",
            custom_id="modal:character_create",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        dto = CreateCharacterDTO(
            name=inter.text_values["name_input"],
            game_system_id=self.game_system_id,
            avatar= inter.text_values["avatar_url_input"] or None
        )

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with character_service_ctx() as character_service:
            await character_service.create(dto, user.id)

        await inter.followup.send("✅ Персонаж успешно создан", ephemeral=True)
