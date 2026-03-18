#app/discord/modals/game_update_modal.py

from disnake import TextInputStyle, ModalInteraction
from disnake.ui import TextInput

from app.discord.dependencies import user_service_ctx, game_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.discord.states.wizards import GameUpdateState
from app.dto import UpdateGameDTO


class GameUpdateModal(BaseModal):
    def __init__(self, state: GameUpdateState):
        self.state=state
        g = state.current_game

        components = [
            TextInput(
                label="Введите имя",
                custom_id="name_input",
                style=TextInputStyle.short,
                min_length=1,
                max_length=255,
                required=True,
                value=g.name if g and g.name else "",
            ),
            TextInput(
                label="Введите id мастера",
                custom_id="gm_id_input",
                style=TextInputStyle.short,
                min_length=0,
                max_length=19,
                required=False,
                value=str(g.gm_id) if g and g.gm_id else "",
            ),
            TextInput(
                label="Введите id роли в дискорде",
                custom_id="discord_role_id_input",
                style=TextInputStyle.short,
                min_length=0,
                max_length=19,
                required=False,
                value=str(g.discord_role_id) if g and g.discord_role_id else "",
            ),
            TextInput(
                label="Введите id главного канала игры",
                custom_id="discord_main_channel_id_input",
                style=TextInputStyle.short,
                min_length=0,
                max_length=19,
                required=False,
                value=str(g.discord_main_channel_id) if g and g.discord_main_channel_id else "",
            ),
        ]
        super().__init__(
            title="Game Update Window",
            custom_id="modal:game_update",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        name = inter.text_values["name_input"]
        gm_id = int(raw) if (raw := inter.text_values["gm_id_input"].strip()) else None
        discord_role_id = int(raw) if (raw := inter.text_values["discord_role_id_input"].strip()) else None
        discord_main_channel_id = int(raw) if (
            raw := inter.text_values["discord_main_channel_id_input"].strip()) else None

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        dto = UpdateGameDTO(
            name=name,
            gm_id=gm_id,
            discord_role_id=discord_role_id,
            discord_main_channel_id=discord_main_channel_id,
            game_system_id=self.state.game_system_id,
        )

        async with game_service_ctx() as game_service:
            await game_service.update(self.state.game_id, dto, user.id)

        await inter.followup.send("✅ Игра успешно обновлена", ephemeral=True)
