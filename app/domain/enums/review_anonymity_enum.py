# app/domain/enums/review_anonymity_enum.py
from enum import Enum

class ReviewAnonymityEnum(str, Enum):
    """
    Режим видимости игрового отзыва.

    Attributes:
        PUBLIC: Публичный отзыв — автор виден
        PRIVATE: Анонимный отзыв — автор скрыт
    """
    PUBLIC  = "public"
    PRIVATE = "private"