#app/domain/repositories/character_repositories/character_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities import Character


class ICharacterRepository(ABC):
    """
        Интерфейс репозитория для работы с персонажами.

        Управляет CRUD операциями персонажей, поддерживает загрузку связанных сущностей
        и фильтрацию по владельцу или игре.

        Методы:
            * create — создаёт нового персонажа и возвращает его с присвоенным ID
            * get_by_id — возвращает персонажа по UUID без загрузки связей
            * get_by_id_with_relations — возвращает персонажа по UUID с полной загрузкой author, game, game_system
            * get_by_user_id — возвращает всех персонажей пользователя по его UUID
            * get_by_game_id — возвращает всех персонажей в игре по UUID игры
            * update — обновляет поля персонажа и возвращает обновлённую сущность
            * soft_delete — помечает персонажа удалённым (deleted_at = now), физически не удаляет
            * restore — снимает метку удаления с персонажа (deleted_at = NULL)
            * delete — физически удаляет персонажа по UUID (только для администраторов)
    """

    @abstractmethod
    async def create(self, character: Character) -> Character: ...

    @abstractmethod
    async def get_by_id(self, character_id: UUID) -> Optional[Character]: ...

    # С полной загрузкой связей: author, game, game_system
    @abstractmethod
    async def get_by_id_with_relations(self, character_id: UUID) -> Optional[Character]: ...

    @abstractmethod
    async def get_all_by_user_id(self, user_id: UUID, offset: int, limit: int, include_deleted: bool = False,
                                 only_deleted: bool = False) -> list[Character]: ...

    @abstractmethod
    async def count_by_user_id(self, user_id: UUID) -> int: ...

    @abstractmethod
    async def get_by_game_id(self, game_id: UUID, offset: int, limit: int) -> list[Character]: ...

    @abstractmethod
    async def count_by_game_id(self, game_id: UUID) -> int: ...

    @abstractmethod
    async def get_by_id_and_game_id(self, character_id: UUID, game_id: UUID) -> Optional[Character]: ...

    @abstractmethod
    async def attach_to_game(self, character_id: UUID, game_id: UUID) -> Character: ...

    @abstractmethod
    async def detach_from_game(self, character_id: UUID) -> None: ...

    @abstractmethod
    async def update(self, character: Character) -> Character: ...

    @abstractmethod
    async def soft_delete(self, character_id: UUID) -> None: ...

    @abstractmethod
    async def restore(self, character_id: UUID) -> None: ...

    @abstractmethod
    async def delete(self, character_id: UUID) -> None: ...