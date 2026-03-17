# app/exceptions/discord_exceptions.py


class DiscordError(Exception):
    """Базовая ошибка Discord-интеграции"""
    pass


class GuildSettingsNotFoundException(DiscordError):
    """Настройки для данного Discord-сервера не найдены"""
    pass


class GameNotFoundByEventTitleException(DiscordError):
    """Игра с названием, совпадающим с заголовком события, не найдена.
    Используется при автоматической привязке Scheduled Event к игре."""
    pass


class SessionAlreadyLinkedToEventException(DiscordError):
    """Сессия уже привязана к Discord Scheduled Event"""
    pass


class EventAlreadyLinkedToSessionException(DiscordError):
    """Данный Discord Scheduled Event уже привязан к другой сессии"""
    pass