# app/domain/enums/review_status_enum.py
from enum import Enum

class ReviewStatusEnum(str, Enum):
    """
    Статус игрового отзыва.

    Attributes:
        CREATED: Отзыв создан, ожидает заполнения игроком
        SEND: Отзыв заполнен и отправлен
        CANCELED: Отзыв так и не был заполнен/отправлен
    """
    CREATED  = "created"
    SEND   = "send"
    CANCELED = "canceled"