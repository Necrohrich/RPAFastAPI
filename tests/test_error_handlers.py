#tests/test_error_handlers.py

import pytest
from unittest.mock import AsyncMock, MagicMock
import disnake

from app.discord.error_handlers import on_slash_command_error
from app.exceptions.auth_exceptions import InvalidToken, TokenExpired
from app.exceptions.common_exceptions import NotFoundError, PermissionDenied


def make_inter(is_done: bool = False) -> MagicMock:
    """Фабрика мок-interaction."""
    inter = MagicMock(spec=disnake.ApplicationCommandInteraction)
    inter.author.id = 123456789
    inter.data.name = "test_command"
    inter.response.is_done.return_value = is_done
    inter.response.send_message = AsyncMock()
    inter.followup.send = AsyncMock()
    return inter


@pytest.mark.asyncio
@pytest.mark.parametrize("exception, expected_title", [
    (InvalidToken(),     "Сессия не найдена"),
    (TokenExpired(),     "Сессия истекла"),
    (NotFoundError(),    "Не найдено"),
    (PermissionDenied(), "Доступ запрещён"),
])
async def test_known_exceptions_send_embed(exception, expected_title):
    inter = make_inter()

    await on_slash_command_error(inter, exception)

    inter.response.send_message.assert_called_once()
    embed = inter.response.send_message.call_args.kwargs["embed"]
    assert expected_title in embed.title


@pytest.mark.asyncio
async def test_unknown_exception_sends_generic_message():
    inter = make_inter()

    await on_slash_command_error(inter, RuntimeError("unexpected"))

    inter.response.send_message.assert_called_once()
    embed = inter.response.send_message.call_args.kwargs["embed"]
    assert "Неизвестная ошибка" in embed.title


@pytest.mark.asyncio
async def test_deferred_interaction_uses_followup():
    inter = make_inter(is_done=True)

    await on_slash_command_error(inter, NotFoundError())

    inter.followup.send.assert_called_once()
    inter.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_command_invoke_error_unwraps_original():
    """Disnake оборачивает исключения в CommandInvokeError — проверяем unwrap."""
    from disnake.ext.commands import CommandInvokeError

    inter = make_inter()
    wrapped = CommandInvokeError(InvalidToken())

    await on_slash_command_error(inter, wrapped)

    embed = inter.response.send_message.call_args.kwargs["embed"]
    assert "Сессия не найдена" in embed.title