#app/discord/views/base_view.py
import disnake
from disnake.ui import View, Item

from app.discord.error_handlers import _handle_error, _resolve_cause


class BaseView(View):
    async def on_error(self, error: Exception, item: Item, interaction: disnake.MessageInteraction) -> None:
        cause = _resolve_cause(error)
        custom_id = getattr(item, "custom_id", repr(item))
        await _handle_error(interaction, cause, f"component={custom_id}")