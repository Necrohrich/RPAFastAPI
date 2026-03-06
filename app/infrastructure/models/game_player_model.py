#app/infrastructure/models/game_player_model.py
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SQLEnum

from app.domain.enums.player_status_enum import PlayerStatusEnum
from app.infrastructure.models import BaseModel

class GamePlayerModel(BaseModel):
    """Ассоциативная модель участия игрока в игре.

       Реализует связь Many-to-Many между User и Game с дополнительным
       полем статуса для системы запросов на вступление.

       Связи:
           * Многие-к-одному: game (Game), user (User)

       Ключевые поля:
           * game_id — игра (FK → games.id)
           * user_id — игрок (FK → users.id)
           * status — статус участия (PENDING/ACCEPTED/REJECTED)
       """
    __tablename__ = 'game_players'

    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('games.id'), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status: Mapped[PlayerStatusEnum] = mapped_column(SQLEnum(PlayerStatusEnum), nullable=False,
                                                     default=PlayerStatusEnum.PENDING)

    # Связи Many-to-One
    game: Mapped["GameModel"] = relationship(back_populates="players") # type: ignore[import]
    user: Mapped["UserModel"] = relationship(back_populates="participated_games") # type: ignore[import]

    __table_args__ = (UniqueConstraint('game_id', 'user_id'),)