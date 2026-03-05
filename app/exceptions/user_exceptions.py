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

class EmailSameAsPrimary(UserError):
    """Secondary Email совпадает с primary"""
    pass

class DiscordAlreadyLinked(UserError):
    """Discord аккаунт уже привязан"""
    pass

class DiscordSameAsPrimary(UserError):
    """Secondary Discord ID совпадает с primary"""
    pass

class PasswordSameError(UserError):
    """Новый пароль совпадает со старым"""
    pass

class PasswordWrongError(UserError):
    """Старый пароль введён неверно"""
    pass