#app/domain/repositories/character_repositories/game_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities import Game
from app.domain.entities import GamePlayer
from app.domain.enums import PlayerStatusEnum

class IGameRepository(ABC):

    @abstractmethod
    async def create(self, game: Game) -> Game: ...

    # Только базовые поля игры
    @abstractmethod
    async def get_by_id(self, game_id: UUID) -> Optional[Game]: ...

    # С полной загрузкой: author, game_system
    @abstractmethod
    async def get_by_id_with_relations(self, game_id: UUID) -> Optional[Game]: ...

    @abstractmethod
    async def get_by_author_id(self, author_id: UUID) -> list[Game]: ...

    @abstractmethod
    async def update(self, game: Game) -> Game: ...

    # Soft delete — проставляет deleted_at
    @abstractmethod
    async def soft_delete(self, game_id: UUID) -> None: ...

    # Restore — обнуляет deleted_at (только для админов)
    @abstractmethod
    async def restore(self, game_id: UUID) -> None: ...

    # --- Игроки ---

    @abstractmethod
    async def get_players(self, game_id: UUID, status: PlayerStatusEnum | None = None) -> list[GamePlayer]: ...

    @abstractmethod
    async def add_player(self, game_player: GamePlayer) -> GamePlayer: ...

    @abstractmethod
    async def update_player_status(self, game_id: UUID, user_id: UUID, status: PlayerStatusEnum) -> GamePlayer: ...

    @abstractmethod
    async def remove_player(self, game_id: UUID, user_id: UUID) -> None: ...