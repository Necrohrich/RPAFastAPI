__all__=[
    "BaseModal",
    "AttachDiscordIdModal",
    "AttachEmailModal",
    "ChangePasswordModal",
    "LoginModal",
    "RegisterModal",
    "SelectSearchModal",
    "CharacterCreateModal",
    "CharacterUpdateModal"
]

from app.discord.modals.attach_email_modal import AttachEmailModal

from app.discord.modals.base_modal import BaseModal

from app.discord.modals.change_password_modal import ChangePasswordModal
from app.discord.modals.character_create_modal import CharacterCreateModal
from app.discord.modals.character_update_modal import CharacterUpdateModal

from app.discord.modals.login_modal import LoginModal

from app.discord.modals.register_modal import RegisterModal

from app.discord.modals.select_search_modal import SelectSearchModal
from app.discord.modals.attach_discord_id_modal import AttachDiscordIdModal