# app/exceptions/auth_exceptions.py

class AuthError(Exception):
    """Базовая ошибка аутентификации"""
    pass

class InvalidCredentials(AuthError):
    """Неверный логин или пароль"""
    pass

class InvalidToken(AuthError):
    """Токен недействителен"""
    pass

class TokenExpired(AuthError):
    """Срок действия токена истёк"""
    pass