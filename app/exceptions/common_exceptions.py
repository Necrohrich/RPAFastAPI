#app/exceptions/common_exceptions.py

class ApplicationError(Exception):
    """Базовая ошибка application слоя"""
    pass

class NotFoundError(ApplicationError):
    """Объект не найден"""
    pass

class ValidationError(ApplicationError):
    """Ошибка валидации"""
    pass