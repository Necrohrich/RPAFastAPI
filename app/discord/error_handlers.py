# app/discord/error_handlers.py
import logging

import disnake
from disnake.ext import commands
from pydantic import ValidationError as PydanticValidationError
from app.exceptions import *

logger = logging.getLogger(__name__)

_ERROR_MAP: dict[type[Exception], tuple[str, str, disnake.Color]] = {
    # ── User exceptions ──────────────────────────────────────
    EmailAlreadyExists: (
        "Email уже занят",
        "Пользователь с таким email уже зарегистрирован.",
        disnake.Color.orange(),
    ),
    EmailSameAsPrimary: (
        "Совпадение Email",
        "Secondary Email совпадает с primary.",
        disnake.Color.orange(),
    ),
    LoginAlreadyExists: (
        "Логин уже занят",
        "Пользователь с таким логином уже существует.",
        disnake.Color.orange(),
    ),
    DiscordAlreadyLinked: (
        "Discord уже привязан",
        "Этот Discord аккаунт уже привязан к другому пользователю.",
        disnake.Color.orange(),
    ),
    DiscordSameAsPrimary: (
        "Совпадение Discord ID",
        "Secondary Discord ID совпадает с primary.",
        disnake.Color.orange(),
    ),
    PasswordSameError: (
        "Совпадение паролей",
        "Новый пароль должен отличаться от текущего.",
        disnake.Color.orange(),
    ),
    PasswordWrongError: (
        "Неверный пароль",
        "Старый пароль введён неверно.",
        disnake.Color.orange(),
    ),
    # ── Auth exceptions ──────────────────────────────────────
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
    # ── Character exceptions ─────────────────────────────────
    CharacterNotFoundException: (
        "Персонаж не найден",
        "Персонаж с указанным ID не найден или был удалён.",
        disnake.Color.yellow(),
    ),
    CharacterAlreadyExistsException: (
        "Персонаж уже существует",
        "Персонаж уже существует в этой игре.",
        disnake.Color.orange(),
    ),
    CharacterGameSystemMismatchException: (
        "Несовместимая игровая система",
        "Игровая система персонажа не совпадает с игровой системой игры.",
        disnake.Color.orange(),
    ),
    CharacterPermissionException: (
        "Нет доступа к персонажу",
        "Вы не являетесь автором этого персонажа.",
        disnake.Color.red(),
    ),
    CharacterGameSystemAlreadySetException: (
        "Система уже привязана",
        "Игровая система уже привязана к персонажу и не может быть изменена.",
        disnake.Color.orange(),
    ),
    CharacterError: (
        "Ошибка персонажа",
        "Произошла ошибка при работе с персонажем. Попробуйте позже.",
        disnake.Color.red(),
    ),
    # ── Game exceptions ──────────────────────────────────────
    GameNotFoundException: (
        "Игра не найдена",
        "Игра с указанным ID не найдена или была удалена.",
        disnake.Color.yellow(),
    ),
    GameAlreadyExistsException: (
        "Игра уже существует",
        "Игра с таким названием уже существует у этого пользователя.",
        disnake.Color.orange(),
    ),
    PlayerAlreadyInGameException: (
        "Игрок уже в игре",
        "Вы уже являетесь участником этой игры или ваша заявка на рассмотрении.",
        disnake.Color.orange(),
    ),
    PlayerNotFoundException: (
        "Игрок не найден",
        "Игрок не найден в составе этой игры.",
        disnake.Color.yellow(),
    ),
    NotGameAuthorException: (
        "Нет прав",
        "Это действие доступно только автору игры.",
        disnake.Color.red(),
    ),
    GameError: (
        "Ошибка игры",
        "Произошла ошибка при работе с игрой. Попробуйте позже.",
        disnake.Color.red(),
    ),
    # ── Game system exceptions ───────────────────────────────
    GameSystemHasDependenciesException: (
        "Невозможно удалить",
        "Игровая система используется персонажами или играми. Сначала удалите связанные объекты.",
        disnake.Color.orange(),
    ),
    GameSystemNotFoundException: (
        "Игровая система не найдена",
        "Игровая система с указанным ID или именем не найдена.",
        disnake.Color.yellow(),
    ),
    GameSystemAlreadyExistsException: (
        "Игровая система уже существует",
        "Игровая система с таким названием уже существует.",
        disnake.Color.orange(),
    ),
    GameSystemError: (
        "Ошибка игровой системы",
        "Произошла ошибка при работе с игровой системой. Попробуйте позже.",
        disnake.Color.red(),
    ),
    # ── Common exceptions ────────────────────────────────────
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


async def _respond(inter, embed: disnake.Embed) -> None:
    try:
        if inter.response.is_done():
            await inter.followup.send(embed=embed, ephemeral=True)
        else:
            await inter.response.send_message(embed=embed, ephemeral=True)
    except disnake.HTTPException as e:
        logger.error("Failed to send error response to user %s: HTTP %s %s", inter.author.id, e.status, e.text)


def _resolve_cause(error: Exception) -> Exception:
    return getattr(error, "original", error)


async def _handle_error(inter, cause: Exception, context: str) -> None:
    if isinstance(cause, PydanticValidationError):
        first_error = cause.errors()[0]
        embed = _build_error_embed("Ошибка валидации", first_error["msg"], disnake.Color.yellow())
        await _respond(inter, embed)
        logger.warning("PydanticValidationError for user %s (%s): %s", inter.author.id, context, cause)
        return

    for exc_type, (title, message, color) in _ERROR_MAP.items():
        if isinstance(cause, exc_type):
            embed = _build_error_embed(title, message, color)
            await _respond(inter, embed)
            logger.warning("Handled %s for user %s (%s): %s", type(cause).__name__, inter.author.id, context, cause)
            return

    logger.exception("Unhandled exception in %s for user %s", context, inter.author.id, exc_info=cause)
    embed = _build_error_embed(
        "Неизвестная ошибка",
        "Произошла непредвиденная ошибка. Мы уже разбираемся с проблемой.",
        disnake.Color.dark_red(),
    )
    await _respond(inter, embed)


# ── Slash commands ──────────────────────────────────────────
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception) -> None:
    cause = _resolve_cause(error)
    await _handle_error(inter, cause, f"command={inter.data.name}")


def setup_error_handlers(bot: commands.InteractionBot) -> None:
    bot.add_listener(on_slash_command_error)
    logger.debug("Discord error handlers registered")