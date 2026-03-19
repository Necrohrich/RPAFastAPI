# app/domain/enums/review_rating_enum.py
from enum import Enum

class ReviewRatingEnum(str, Enum):
    """
    Оценка игровой сессии.

    Attributes:
        TERRIBLE: Ужасно (😡)
        BAD: Есть осадок (😕)
        NEUTRAL: Нейтрально (😐)
        GOOD: Хорошо (🙂)
        EXCELLENT: Превосходно (🤩)
    """
    TERRIBLE  = "terrible"
    BAD       = "bad"
    NEUTRAL   = "neutral"
    GOOD      = "good"
    EXCELLENT = "excellent"