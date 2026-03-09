#app/exceptions/character_exceptions.py

class CharacterError(Exception):
    """Базовая ошибка персонажа"""
    pass

class CharacterNotFoundException(CharacterError):
    """Персонаж с указанным ID не найден или был удалён"""
    pass

class CharacterAlreadyExistsException(CharacterError):
    """Персонаж с таким именем уже существует в этой игре"""
    pass

class CharacterGameSystemMismatchException(CharacterError):
    """Игровая система персонажа не совпадает с игровой системой игры"""
    pass

class CharacterPermissionException(CharacterError):
    """Отправитель запроса не является автором персонажа"""
    pass

class CharacterGameSystemAlreadySetException(CharacterError):
    """Игровая система уже привязана к персонажу и не может быть изменена"""
    pass