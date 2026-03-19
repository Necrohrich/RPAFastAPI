# app/domain/enums/review_scene_type_enum.py
from enum import Enum

class ReviewSceneTypeEnum(str, Enum):
    """
    Тип игровой сцены, упомянутой в отзыве.

    Attributes:
        COMEDY:   Комедия
        HORROR:   Хоррор
        ACTION:   Экшен
        DRAMA:    Драма
        ROMANCE:  Романтика
    """
    COMEDY  = "comedy"
    HORROR  = "horror"
    ACTION  = "action"
    DRAMA   = "drama"
    ROMANCE = "romance"