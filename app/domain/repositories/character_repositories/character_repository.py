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
            * delete — физически удаляет персонажа по UUID
    """

    @abstractmethod
    async def create(self, character: Character) -> Character: ...

    @abstractmethod
    async def get_by_id(self, character_id: UUID) -> Optional[Character]: ...

    # С полной загрузкой связей: author, game, game_system
    @abstractmethod
    async def get_by_id_with_relations(self, character_id: UUID) -> Optional[Character]: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Character]: ...

    @abstractmethod
    async def get_by_game_id(self, game_id: UUID) -> list[Character]: ...

    @abstractmethod
    async def update(self, character: Character) -> Character: ...

    @abstractmethod
    async def delete(self, character_id: UUID) -> None: ...