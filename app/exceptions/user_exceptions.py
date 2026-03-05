# app/exceptions/user_exceptions.py

class UserError(Exception):
    """Базовая ошибка пользовательского слоя"""
    pass

class LoginAlreadyExists(UserError):
    """Логин уже занят"""
    pass

class EmailAlreadyExists(UserError):
    """Email уже используется"""
    pass

class DiscordAlreadyLinked(UserError):
    """Discord аккаунт уже привязан"""
    pass

class PasswordSameError(UserError):
    """Новый пароль совпадает со старым"""
    pass

class PasswordWrongError(UserError):
    """Старый пароль введён неверно"""
    pass