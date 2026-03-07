#app/exceptions/game_exceptions.py

class GameError(Exception):
    """Базовая ошибка игры"""
    pass

class GameNotFoundException(GameError):
    """Игра с указанным ID не найдена или была удалена"""
    pass

class GameAlreadyExistsException(GameError):
    """Игра с таким названием уже существует у этого пользователя"""
    pass

class PlayerAlreadyInGameException(GameError):
    """Пользователь уже является участником этой игры или его заявка на рассмотрении"""
    pass

class PlayerNotFoundException(GameError):
    """Игрок не найден в составе этой игры"""
    pass

class NotGameAuthorException(GameError):
    """Операция доступна только автору игры"""
    pass