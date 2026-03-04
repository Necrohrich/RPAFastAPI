#app/discord/modals/base_modal.py
import disnake
from disnake.ui import Modal

from app.discord.error_handlers import _handle_error, _resolve_cause


class BaseModal(Modal):
    async def _scheduled_task(self, interaction: disnake.ModalInteraction) -> None:
        try:
            await self.callback(interaction)
        except Exception as e:
            cause = _resolve_cause(e)
            await _handle_error(interaction, cause, f"modal={self.custom_id}")