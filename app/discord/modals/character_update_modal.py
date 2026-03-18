#app/discord/modals/character_update_modal.py

from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import character_service_ctx, user_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.discord.states.wizards import CharacterUpdateState
from app.dto import UpdateCharacterDTO


class CharacterUpdateModal(BaseModal):
    def __init__(self, state: CharacterUpdateState):
        self.state=state
        c = state.current_character

        components = [
            TextInput(
                label="Введите имя",
                custom_id="name_input",
                style=TextInputStyle.short,
                min_length=1,
                max_length=255,
                required=True,
                value=c.name if c and c.name else "",
            ),
            TextInput(
                label="Введите url аватара",
                custom_id="avatar_url_input",
                style=TextInputStyle.short,
                min_length=10,
                max_length=255,
                required=False,
                value=c.avatar if c and c.avatar else "",
            ),
        ]
        super().__init__(
            title="Character Update Window",
            custom_id="modal:character_update",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        name = inter.text_values["name_input"]
        avatar = inter.text_values["avatar_url_input"].strip() or None

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        dto = UpdateCharacterDTO(
            name=name,
            avatar=avatar,
            game_system_id=self.state.game_system_id,
        )

        async with character_service_ctx() as character_service:
            await character_service.update(self.state.character_id, dto, user.id)

        await inter.followup.send("✅ Персонаж успешно обновлён", ephemeral=True)
