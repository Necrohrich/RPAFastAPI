#app/discord/cogs/character_cog.py
from uuid import UUID

from disnake import ApplicationCommandInteraction, User, MessageInteraction
from disnake.ext import commands

from app.discord.dependencies import user_service_ctx, character_service_ctx
from app.discord.embeds.build_сharacter_embed import build_character_embed
from app.discord.policies import require_role, discord_policy
from app.discord.states import ActiveCharacterEntry
from app.discord.states.active_characters import set_active, clear_active
from app.discord.views import CharacterView, SelectView
from app.domain.policies import PlatformPolicies

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="character", description="Команды для работы с персонажем")
    async def character(self, inter: ApplicationCommandInteraction) -> None: ...

    @character.sub_command(name="menu", description="Показать меню создания персонажа [SUPPORT]")
    @require_role(PlatformPolicies.require_support)
    async def menu(
            self,
            inter: ApplicationCommandInteraction,
    ) -> None:
        embed, file = build_character_embed()

        await inter.send(embed=embed, file=file, view=CharacterView())

    @character.sub_command(name="restore", description=" Восстановить удаленного персонажа [MODERATOR]")
    @require_role(PlatformPolicies.require_moderator)
    async def restore(
            self,
            inter: ApplicationCommandInteraction,
            user: User
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(user.id)

        async with character_service_ctx() as character_service:
            characters = await character_service.get_list_by_user_id(user.id, only_deleted=True)

        async def on_character_selected(cb_inter: MessageInteraction, character_id: UUID):
            async with character_service_ctx() as cs:
                await cs.restore(character_id)
            await cb_inter.followup.send("✅ Персонаж успешно восстановлен", ephemeral=True)

        view = SelectView(
            items=characters,
            display_field="name",
            title="Персонажи",
            callback=on_character_selected,
            skippable=False
        )
        await inter.followup.send("Выберите персонажа:", view=view, ephemeral=True)

    @character.sub_command(name="delete", description="Удалить выбранного персонажа пользователя [SUPERADMIN]")
    @require_role(PlatformPolicies.require_superadmin)
    async def delete(
            self,
            inter: ApplicationCommandInteraction,
            user: User
    ) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(user.id)

        async with character_service_ctx() as character_service:
            characters = await character_service.get_list_by_user_id(user.id, include_deleted=True)

        async def on_character_selected(cb_inter: MessageInteraction, character_id: UUID):
            async with character_service_ctx() as cs:
                await cs.delete(character_id)
            await cb_inter.followup.send("✅ Персонаж успешно удален", ephemeral=True)

        view = SelectView(
            items=characters,
            display_field="name",
            title="Персонажи",
            callback=on_character_selected,
            skippable=False
        )
        await inter.followup.send("Выберите персонажа:", view=view, ephemeral=True)

    #----------------------------------
    # Character activation/deactivation
    # ---------------------------------

    @character.sub_command(name="become", description="Стать персонажем (активировать)")
    @discord_policy()
    async def become(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)

        async with user_service_ctx() as user_service:
            user = await user_service.get_user_by_discord(inter.author.id)
            characters = await user_service.get_my_characters_list(user.id)

        async def on_selected(cb_inter: MessageInteraction, character_id: str):
            char = next(c for c in characters if str(c.id) == character_id)
            set_active(inter.author.id, ActiveCharacterEntry(
                character_id=char.id,
                character_name=char.name,
                avatar_url=char.avatar,
            ))
            await cb_inter.followup.send(
                f"✅ Теперь ты **{char.name}**.",
                ephemeral=True
            )

        view = SelectView(items=characters, display_field="name",
                          title="Персонажи", callback=on_selected, skippable=False)
        await inter.followup.send("Выберите персонажа:", view=view, ephemeral=True)

    @character.sub_command(name="leave", description="Перестать быть персонажем")
    async def leave(self, inter: ApplicationCommandInteraction) -> None:
        clear_active(inter.author.id)
        await inter.send("✅ Ты снова пишешь от своего имени.", ephemeral=True)



