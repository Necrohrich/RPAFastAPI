# app/discord/cogs/roleplay_cog.py
import disnake
from disnake.ext import commands
from app.discord.states.active_characters import get_active
from app.discord.utils.validator_utils import is_valid_url


class RoleplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._webhook_cache: dict[int, disnake.Webhook] = {}

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Игнорируем ботов
        if message.author.bot:
            return

        entry = get_active(message.author.id)
        if entry is None:
            return  # пользователь не активировал персонажа — пишет как обычно

        if not message.content and not message.attachments:
            await message.channel.send(
                f"{message.author.mention} стикеры от лица персонажа не поддерживаются",
                delete_after=5
            )
            return

        files = [await a.to_file() for a in message.attachments]

        # Удаляем оригинальное сообщение
        try:
            await message.delete()
        except disnake.Forbidden:
            return
        except disnake.NotFound:
            pass

        # Получаем или создаём вебхук для канала
        webhook = await self._get_or_create_webhook(message.channel)
        if webhook is None:
            return

        # Определяем thread_id для форумных веток
        thread = None
        if isinstance(message.channel, disnake.Thread):
            thread = message.channel

        kwargs = dict(
            content=message.content,
            username=entry.character_name,
            avatar_url=entry.avatar_url if is_valid_url(entry.avatar_url) else None,
            files=files,
        )
        if isinstance(message.channel, disnake.Thread):
            kwargs["thread"] = message.channel

        await webhook.send(**kwargs)

    async def _get_or_create_webhook(self, channel) -> disnake.Webhook | None:
        """Кэшируем вебхук по каналу, чтобы не создавать каждый раз."""
        target_channel = channel.parent if isinstance(channel, disnake.Thread) else channel

        if target_channel.id in self._webhook_cache:
            return self._webhook_cache[target_channel.id]

        try:
            webhooks = await target_channel.webhooks()
            for wh in webhooks:
                if wh.user == self.bot.user:
                    self._webhook_cache[target_channel.id] = wh
                    return wh
            wh = await target_channel.create_webhook(name="RoleplayBot")
            self._webhook_cache[target_channel.id] = wh
            return wh
        except (disnake.Forbidden, disnake.HTTPException):
            return None