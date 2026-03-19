# app/exceptions/game_review_exceptions.py


class GameReviewError(Exception):
    """Базовая ошибка игрового отзыва"""
    pass


class GameReviewNotFoundException(GameReviewError):
    """Игровой отзыв с указанным ID не найден"""
    pass


class GameReviewAlreadyExistsException(GameReviewError):
    """Игрок уже оставил отзыв на эту сессию"""
    pass


class GameReviewAlreadySentException(GameReviewError):
    """Отзыв уже был отправлен и не может быть изменён"""
    pass


class GameReviewNotAllowedException(GameReviewError):
    """Пользователь не имеет права оставить отзыв (не игрок или не присутствовал)"""
    pass


class GameReviewInvalidStatusTransitionException(GameReviewError):
    """Недопустимый переход статуса отзыва"""
    pass