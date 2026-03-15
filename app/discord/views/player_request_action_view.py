# app/discord/views/player_request_action_view.py
from uuid import UUID
from disnake import MessageInteraction, ButtonStyle, NotFound, Embed, Color, Forbidden
from disnake.ui import button, Button

from app.discord.dependencies import game_service_ctx, user_service_ctx
from app.discord.views.base_view import BaseView


class PlayerRequestActionView(BaseView):
    def __init__(self, game_id: UUID, player_id: UUID):
        super().__init__(timeout=180)
        self.game_id = game_id
        self.player_id = player_id

    @staticmethod
    async def _get_requester(inter: MessageInteraction) -> UUID:
        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
        return user.id

    async def _notify_player(self, inter: MessageInteraction, accepted: bool) -> None:
        async with user_service_ctx() as user_service:
            player = await user_service.get_by_id(self.player_id)

        if not player or not player.primary_discord_id:
            return

        discord_user = inter.bot.get_user(player.primary_discord_id)
        if discord_user is None:
            try:
                discord_user = await inter.bot.fetch_user(player.primary_discord_id)
            except NotFound:
                return

        async with game_service_ctx() as game_service:
            game = await game_service.get_by_id(self.game_id)

        if accepted:
            embed = Embed(
                title="✅ Заявка одобрена",
                description=f"Ваша заявка на вступление в игру **{game.name}** была одобрена.",
                color=Color.green()
            )
        else:
            embed = Embed(
                title="❌ Заявка отклонена",
                description=f"Ваша заявка на вступление в игру **{game.name}** была отклонена.",
                color=Color.red()
            )

        try:
            await discord_user.send(embed=embed)
        except Forbidden:
            pass

    @button(label="✅ Одобрить", style=ButtonStyle.success, custom_id="player_request:approve")
    async def approve_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        requester_id = await self._get_requester(inter)
        async with game_service_ctx() as game_service:
            await game_service.approve_join(self.game_id, self.player_id, requester_id)

        await self._notify_player(inter, accepted=True)
        await inter.followup.send("✅ Заявка одобрена", ephemeral=True)

    @button(label="❌ Отклонить", style=ButtonStyle.danger, custom_id="player_request:reject")
    async def reject_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        requester_id = await self._get_requester(inter)
        async with game_service_ctx() as game_service:
            await game_service.reject_join(self.game_id, self.player_id, requester_id)

        await self._notify_player(inter, accepted=False)
        await inter.followup.send("❌ Заявка отклонена", ephemeral=True)

    @button(label="⏭ Пропустить", style=ButtonStyle.secondary, custom_id="player_request:skip")
    async def skip_button(self, _: Button, inter: MessageInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await inter.delete_original_response()

