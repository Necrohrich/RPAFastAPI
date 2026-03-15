#app/discord/modals/game_create_modal.py
from uuid import UUID

from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import user_service_ctx, game_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.dto import CreateGameDTO


class GameCreateModal(BaseModal):
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
                label="Введите id мастера",
                custom_id="gm_id_input",
                style=TextInputStyle.short,
                min_length=17,
                max_length=18,
                required=False
            ),
            TextInput(
                label="Введите id роли в дискорде",
                custom_id="discord_role_id_input",
                style=TextInputStyle.short,
                min_length=17,
                max_length=18,
                required=False
            ),
            TextInput(
                label="Введите id главного канала игры",
                custom_id="discord_main_channel_id_input",
                style=TextInputStyle.short,
                min_length=17,
                max_length=18,
                required=False
            ),
        ]
        super().__init__(
            title="Game Create Window",
            custom_id="modal:game_create",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        dto = CreateGameDTO(
            name=inter.text_values["name_input"],
            game_system_id=self.game_system_id,
            gm_id=int(inter.text_values["gm_id_input"]) if inter.text_values["gm_id_input"] else None,
            discord_role_id=int(inter.text_values["discord_role_id_input"]) if inter.text_values[
                "discord_role_id_input"] else None,
            discord_main_channel_id=int(inter.text_values["discord_main_channel_id_input"]) if inter.text_values[
                "discord_main_channel_id_input"] else None,
        )

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with game_service_ctx() as game_service:
            await game_service.create(dto, user.id)

        await inter.followup.send("✅ Игра успешно создана", ephemeral=True)
