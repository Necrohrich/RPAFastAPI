# app/discord/error_handlers.py
import logging

import disnake
from disnake.ext import commands

from app.exceptions.auth_exceptions import (
    AuthError,
    InvalidCredentials,
    InvalidToken,
    TokenExpired,
)
from app.exceptions.common_exceptions import (
    ApplicationError,
    NotFoundError,
    ValidationError,
    PermissionDenied,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Mapping: exception class -> (title, message, color)
# ──────────────────────────────────────────────
_ERROR_MAP: dict[type[Exception], tuple[str, str, disnake.Color]] = {
    # Auth exceptions
    InvalidCredentials: (
        "Неверные данные",
        "Логин или пароль указаны неверно.",
        disnake.Color.orange(),
    ),
    InvalidToken: (
        "Сессия не найдена",
        "Ваша сессия не найдена или недействительна. Пожалуйста, выполните `/login`.",
        disnake.Color.orange(),
    ),
    TokenExpired: (
        "Сессия истекла",
        "Срок действия вашей сессии истёк. Пожалуйста, выполните `/login` повторно.",
        disnake.Color.orange(),
    ),
    AuthError: (
        "Ошибка аутентификации",
        "Произошла ошибка при аутентификации. Попробуйте позже.",
        disnake.Color.orange(),
    ),
    # Common application exceptions
    NotFoundError: (
        "Не найдено",
        "Запрошенный объект не найден.",
        disnake.Color.yellow(),
    ),
    ValidationError: (
        "Ошибка валидации",
        "Переданные данные некорректны. Проверьте введённые значения.",
        disnake.Color.yellow(),
    ),
    PermissionDenied: (
        "Доступ запрещён",
        "У вас недостаточно прав для выполнения этого действия.",
        disnake.Color.red(),
    ),
    ApplicationError: (
        "Ошибка приложения",
        "Произошла внутренняя ошибка приложения. Попробуйте позже.",
        disnake.Color.red(),
    ),
}

def _build_error_embed(title: str, description: str, color: disnake.Color) -> disnake.Embed:
    return disnake.Embed(title=f"❌ {title}", description=description, color=color)

async def _respond(
    inter: disnake.ApplicationCommandInteraction,
    embed: disnake.Embed,
) -> None:
    """Отвечает на interaction, учитывая, было ли оно уже подтверждено (deferred)."""
    try:
        if inter.response.is_done():
            await inter.followup.send(embed=embed, ephemeral=True)
        else:
            await inter.response.send_message(embed=embed, ephemeral=True)
    except disnake.HTTPException as e:
        logger.error(
            "Failed to send error response to user %s: HTTP %s %s",
            inter.author.id,
            e.status,
            e.text,
        )


async def on_slash_command_error(
    inter: disnake.ApplicationCommandInteraction,
    error: Exception,
) -> None:
    """
    Глобальный обработчик ошибок slash-команд.

    Подключение к боту:
        bot.add_listener(on_slash_command_error)
    """
    # Disnake оборачивает исходное исключение в CommandInvokeError
    cause = getattr(error, "original", error)

    # Ищем наиболее конкретный тип исключения в таблице
    for exc_type, (title, message, color) in _ERROR_MAP.items():
        if isinstance(cause, exc_type):
            embed = _build_error_embed(title, message, color)
            await _respond(inter, embed)
            logger.warning(
                "Handled %s for user %s (command=%s): %s",
                type(cause).__name__,
                inter.author.id,
                inter.data.name,
                cause,
            )
            return

    # Необработанное исключение — логируем полный traceback
    logger.exception(
        "Unhandled exception in command '%s' for user %s",
        inter.data.name,
        inter.author.id,
        exc_info=cause,
    )
    embed = _build_error_embed(
        "Неизвестная ошибка",
        "Произошла непредвиденная ошибка. Мы уже разбираемся с проблемой.",
        disnake.Color.dark_red(),
    )
    await _respond(inter, embed)


def setup_error_handlers(bot: commands.InteractionBot) -> None:
    """
    Регистрирует все обработчики ошибок на экземпляре бота.

    Использование в bot.py::

        from app.discord.error_handlers import setup_error_handlers

        async def setup_hook(self):
            await load_cogs(self)
            setup_error_handlers(self)
    """
    bot.add_listener(on_slash_command_error)
    logger.debug("Discord error handlers registered")