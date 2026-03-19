# app/discord/views/game_invitation_view.py
from disnake import MessageInteraction, ButtonStyle, Embed, Color, NotFound, Forbidden
from disnake.ui import Button
from uuid import UUID

from app.discord.dependencies import game_service_ctx, user_service_ctx
from app.discord.views.base_view import BaseView


class GameInvitationView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)

        btn = Button(
            label="✅ Принять",
            style=ButtonStyle.success,
            custom_id=f"game_invitation:accept"
        )
        btn.callback = self._on_accept
        self.add_item(btn)

    @staticmethod
    async def _on_accept(inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        game_id = UUID(inter.message.embeds[0].footer.text)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)

        async with game_service_ctx() as game_service:
            game = await game_service.get_by_id(game_id)
            await game_service.request_join(game_id, user.id)

        await inter.followup.send("✅ Заявка на вступление отправлена", ephemeral=True)

        embed = Embed(
            title="Новая заявка",
            description=f"Получена заявка на вступление в игру **{game.name}** от <@{inter.author.id}>.",
            color=Color.blue()
        )

        gm = inter.bot.get_user(game.gm_id)
        if gm is None:
            try:
                gm = await inter.bot.fetch_user(game.gm_id)
            except NotFound:
                return

        try:
            await gm.send(embed=embed)
        except Forbidden:
            pass



