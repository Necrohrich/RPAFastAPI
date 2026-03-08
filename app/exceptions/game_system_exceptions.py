#app/exceptions/game_system_exceptions.py

class GameSystemError(Exception):
    """Базовая ошибка игровой системы"""
    pass

class GameSystemNotFoundException(GameSystemError):
    """Игровая система с указанным ID или именем не найдена"""
    pass

class GameSystemAlreadyExistsException(GameSystemError):
    """Игровая система с таким названием уже существует"""
    pass

class GameSystemHasDependenciesException(GameSystemError):
    """Игровая система используется персонажами или играми"""
    pass