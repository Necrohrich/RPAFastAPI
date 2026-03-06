#app/domain/enums/player_status_enum.py
from enum import Enum


class PlayerStatusEnum(str, Enum):
    """
    Статус участия игрока в игре.

    Attributes:
        PENDING: Запрос на вступление отправлен, ожидает одобрения GM
        ACCEPTED: GM принял игрока в игру
        REJECTED: GM отклонил запрос на вступление
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"