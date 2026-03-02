# app/exceptions/auth_exceptions.py

class AuthError(Exception):
    """Базовая ошибка аутентификации"""
    pass

class InvalidCredentials(AuthError):
    pass

class InvalidToken(AuthError):
    pass

class TokenExpired(AuthError):
    pass