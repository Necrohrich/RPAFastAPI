#tests/test_path_view_modals.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.discord.modals.attach_email_modal import AttachEmailModal
from app.discord.modals.change_password_modal import ChangePasswordModal
from app.exceptions.user_exceptions import (
    DiscordAlreadyLinked,
    DiscordSameAsPrimary,
    EmailAlreadyExists,
    EmailSameAsPrimary,
)
from app.exceptions.auth_exceptions import InvalidToken
from app.exceptions.common_exceptions import NotFoundError


def make_inter(text_values: dict) -> MagicMock:
    """Создаёт мок ModalInteraction с нужными text_values и author."""
    inter = MagicMock()
    inter.text_values = text_values
    inter.author.id = 123456789012345678
    inter.response.defer = AsyncMock()
    inter.followup.send = AsyncMock()
    return inter


def make_user(user_id=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    return user

# ──────────────────────────────────────────────────────────────
# AttachEmailModal
# ──────────────────────────────────────────────────────────────

class TestAttachEmailModal:

    @pytest.mark.asyncio
    async def test_success(self):
        inter = make_inter({"email_input": "secondary@example.com"})
        user = make_user()

        with patch("app.discord.modals.attach_email_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.attach_secondary_email = AsyncMock()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            await AttachEmailModal().callback(inter)

        svc.attach_secondary_email.assert_awaited_once_with(user.id, "secondary@example.com")
        inter.followup.send.assert_awaited_once_with("✅ Email успешно привязан", ephemeral=True)

    @pytest.mark.asyncio
    async def test_email_already_exists(self):
        inter = make_inter({"email_input": "taken@example.com"})
        user = make_user()

        with patch("app.discord.modals.attach_email_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.attach_secondary_email.side_effect = EmailAlreadyExists()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(EmailAlreadyExists):
                await AttachEmailModal().callback(inter)

    @pytest.mark.asyncio
    async def test_email_same_as_primary(self):
        inter = make_inter({"email_input": "primary@example.com"})
        user = make_user()

        with patch("app.discord.modals.attach_email_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.attach_secondary_email.side_effect = EmailSameAsPrimary()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(EmailSameAsPrimary):
                await AttachEmailModal().callback(inter)

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        inter = make_inter({"email_input": "someone@example.com"})

        with patch("app.discord.modals.attach_email_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.side_effect = NotFoundError()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(NotFoundError):
                await AttachEmailModal().callback(inter)


# ──────────────────────────────────────────────────────────────
# ChangePasswordModal
# ──────────────────────────────────────────────────────────────

class TestChangePasswordModal:

    @pytest.mark.asyncio
    async def test_success(self):
        inter = make_inter({
            "old_password_input": "OldPass123!",
            "new_password_input": "NewPass456!",
        })
        user = make_user()

        with patch("app.discord.modals.change_password_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.change_password = AsyncMock()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            await ChangePasswordModal().callback(inter)

        svc.change_password.assert_awaited_once()
        inter.followup.send.assert_awaited_once_with("✅ Пароль успешно изменен", ephemeral=True)

    @pytest.mark.asyncio
    async def test_password_same_error(self):
        from app.exceptions.user_exceptions import PasswordSameError
        inter = make_inter({
            "old_password_input": "SamePass123!",
            "new_password_input": "SamePass123!",
        })
        user = make_user()

        with patch("app.discord.modals.change_password_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.change_password.side_effect = PasswordSameError()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PasswordSameError):
                await ChangePasswordModal().callback(inter)

    @pytest.mark.asyncio
    async def test_password_wrong_error(self):
        from app.exceptions.user_exceptions import PasswordWrongError
        inter = make_inter({
            "old_password_input": "WrongOld123!",
            "new_password_input": "NewPass456!",
        })
        user = make_user()

        with patch("app.discord.modals.change_password_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.return_value = user
            svc.change_password.side_effect = PasswordWrongError()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PasswordWrongError):
                await ChangePasswordModal().callback(inter)

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        inter = make_inter({
            "old_password_input": "OldPass123!",
            "new_password_input": "NewPass456!",
        })

        with patch("app.discord.modals.change_password_modal.user_service_ctx") as ctx:
            svc = AsyncMock()
            svc.get_user_by_discord.side_effect = NotFoundError()
            ctx.return_value.__aenter__ = AsyncMock(return_value=svc)
            ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(NotFoundError):
                await ChangePasswordModal().callback(inter)