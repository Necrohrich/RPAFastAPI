#app/infrastructure/models/game_model.py
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, UUID, ForeignKey, UniqueConstraint

from app.infrastructure.models.base_model import BaseModel


class GameModel(BaseModel):
    """Модель, описывающая игру

    Хранит игры пользователей с Discord интеграцией и системами правил.

    Связи:
        * Многие-к-одному: author (User), game_system (GameSystem)
        * Один-ко-многим: characters, game_sessions, players

    Ключевые поля:
        * name — название игры, уникальное для каждого пользователя
        * author_id — создатель (FK → users.id)
        * discord_role_id — роль Discord для участников
        * game_system_id — система правил (D&D, Pathfinder)
    """
    __tablename__ = 'games'

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    gm_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    discord_role_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    discord_main_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    game_system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('game_systems.id'),
        nullable=False,
        index=True
    )

    #Связи Many-to-One
    author: Mapped["UserModel"] = relationship(back_populates='games') # type: ignore[import]
    game_system: Mapped["GameSystemModel"] = relationship(back_populates='games') # type: ignore[import]

    # Связи One-to-Many
    characters: Mapped[list["CharacterModel"]] = relationship(back_populates='game') # type: ignore[import]
    game_sessions: Mapped[list["GameSessionModel"]] = relationship(back_populates='game') # type: ignore[import]
    players: Mapped[list["GamePlayerModel"]] = relationship(back_populates="game") # type: ignore[import]

    __table_args__ = (
        UniqueConstraint('name', 'author_id', name='uq_game_name_author'),
    )