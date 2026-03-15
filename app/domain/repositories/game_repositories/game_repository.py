# app/domain/repositories/game_repositories/game_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import Game, GamePlayer
from app.domain.enums import PlayerStatusEnum


class IGameRepository(ABC):
    """
    Интерфейс репозитория для работы с играми и их участниками.

    Управляет CRUD операциями игр и составом игроков. Все методы чтения автоматически
    исключают удалённые игры (deleted_at IS NOT NULL).

    Методы:
        * create — создаёт новую игру и возвращает её с присвоенным ID
        * get_by_id — возвращает активную игру по UUID без загрузки связей
        * get_by_id_with_relations — возвращает активную игру по UUID с загрузкой author, game_system
        * get_by_author_id — возвращает игры пользователя по его UUID; поддерживает фильтрацию по deleted_at через include_deleted и only_deleted
        * count_by_author_id — возвращает число игр пользователя; поддерживает те же флаги
        * get_by_name_and_author_id — возвращает игру по названию и UUID автора
        * update — обновляет поля игры и возвращает обновлённую сущность
        * soft_delete — помечает игру удалённой (deleted_at = now), физически не удаляет
        * restore — снимает метку удаления с игры (deleted_at = NULL), только для администраторов
        * delete — физически удаляет игру по UUID, только для администраторов

    Игроки:
        * get_player — возвращает участника игры по UUID игры и UUID пользователя
        * get_players — возвращает список участников игры, опционально фильтруя по статусу
        * count_players — возвращает число участников игры, опционально фильтруя по статусу
        * add_player — добавляет игрока в игру со статусом PENDING
        * update_player_status — обновляет статус участника (ACCEPTED/REJECTED)
        * remove_player — удаляет игрока из игры физически
    """

    @abstractmethod
    async def create(self, game: Game) -> Game: ...

    # Только базовые поля игры
    @abstractmethod
    async def get_by_id(self, game_id: UUID) -> Optional[Game]: ...

    @abstractmethod
    async def get_by_id_include_deleted(self, game_id: UUID) -> Optional[Game]: ...

    # С полной загрузкой: author, game_system
    @abstractmethod
    async def get_by_id_with_relations(self, game_id: UUID) -> Optional[Game]: ...

    @abstractmethod
    async def get_by_author_id(
            self, author_id: UUID, offset: int, limit: int,
            include_deleted: bool = False, only_deleted: bool = False
    ) -> list[Game]: ...

    @abstractmethod
    async def count_by_author_id(
            self, author_id: UUID,
            include_deleted: bool = False, only_deleted: bool = False
    ) -> int: ...

    @abstractmethod
    async def get_by_name_and_author_id(self, author_id: UUID, name: str) -> Optional[Game]: ...

    @abstractmethod
    async def update(self, game: Game) -> Game: ...

    # Soft delete — проставляет deleted_at
    @abstractmethod
    async def soft_delete(self, game_id: UUID) -> None: ...

    # Restore — обнуляет deleted_at (только для админов)
    @abstractmethod
    async def restore(self, game_id: UUID) -> None: ...

    @abstractmethod
    async def delete(self, game_id: UUID) -> None: ...

    # --- Игроки ---
    @abstractmethod
    async def get_player(self, game_id: UUID, user_id: UUID) -> Optional[GamePlayer]: ...

    @abstractmethod
    async def get_players(
        self, game_id: UUID, status: Optional[PlayerStatusEnum], offset: int, limit: int
    ) -> list[GamePlayer]: ...

    @abstractmethod
    async def count_players(self, game_id: UUID, status: Optional[PlayerStatusEnum] = None) -> int: ...

    @abstractmethod
    async def add_player(self, game_player: GamePlayer) -> GamePlayer: ...

    @abstractmethod
    async def update_player_status(
        self, game_id: UUID, user_id: UUID, status: PlayerStatusEnum
    ) -> GamePlayer: ...

    @abstractmethod
    async def remove_player(self, game_id: UUID, user_id: UUID) -> None: ...