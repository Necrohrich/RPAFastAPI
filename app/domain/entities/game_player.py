#app/domain/entities/game_player.py
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity
from app.domain.enums.player_status_enum import PlayerStatusEnum


@dataclass(kw_only=True)
class GamePlayer(BaseEntity):
    """
    Доменная сущность участия игрока в игре.

    Связывает пользователя с игрой и хранит статус его участия.
    Создаётся при отправке запроса на вступление, обновляется GM при одобрении или отказе.

    Attributes:
        game_id: UUID игры
        user_id: UUID пользователя-игрока
        status: Текущий статус участия (PENDING/ACCEPTED/REJECTED)
    """
    game_id: UUID
    user_id: UUID
    status: PlayerStatusEnum