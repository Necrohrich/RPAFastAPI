#app/discord/modals/game_invitation_create_modal.py
from uuid import UUID

from disnake import TextInputStyle, ModalInteraction, Embed
from disnake.ui import TextInput

from app.discord.dependencies import game_service_ctx
from app.discord.modals.base_modal import BaseModal
from app.discord.views import GameInvitationView


class GameInvitationCreateModal(BaseModal):
    def __init__(self, game_id: UUID):
        self.game_id=game_id
        components = [
            TextInput(
                label="Введите id канала",
                custom_id="channel_id_input",
                style=TextInputStyle.short,
                placeholder="Сюда отправится приглашение",
                min_length=17,
                max_length=18
            ),
            TextInput(
                label="Введите текст приглашения",
                custom_id="description_input",
                style=TextInputStyle.long,
                max_length=4000,
                required=False
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
            title="Game Invitation Editor Window",
            custom_id="modal:game_invitation_create",
            components=components,
        )

    async def callback(self, inter: ModalInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with game_service_ctx() as game_service:
            game = await game_service.get_by_id(self.game_id)

        channel_id = int(inter.text_values["channel_id_input"])
        description = inter.text_values["description_input"] or None
        avatar_url = inter.text_values["avatar_url_input"] or None

        channel = inter.bot.get_channel(channel_id)
        if channel is None:
            await inter.followup.send("❌ Канал не найден", ephemeral=True)
            return

        permissions = channel.permissions_for(inter.author)
        if not permissions.send_messages:
            await inter.followup.send("❌ У вас нет прав для отправки сообщений в этот канал", ephemeral=True)
            return

        embed = Embed(title=f"Приглашение в игру: {game.name}")
        if description:
            embed.description = description
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        view = GameInvitationView(game_id=self.game_id)
        await channel.send(embed=embed, view=view)
        await inter.followup.send("✅ Приглашение отправлено", ephemeral=True)


