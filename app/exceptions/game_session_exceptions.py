# app/exceptions/game_session_exceptions.py


class GameSessionError(Exception):
    """Базовая ошибка игровой сессии"""
    pass


class GameSessionNotFoundException(GameSessionError):
    """Игровая сессия с указанным ID не найдена"""
    pass


class GameSessionAlreadyActiveException(GameSessionError):
    """Для этой игры уже существует активная сессия"""
    pass


class GameSessionInvalidStatusTransitionException(GameSessionError):
    """Недопустимый переход статуса сессии"""
    pass


class GameSessionPermissionException(GameSessionError):
    """Недостаточно прав для выполнения операции над сессией"""
    pass