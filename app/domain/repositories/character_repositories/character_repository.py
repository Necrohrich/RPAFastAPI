#app/domain/repositories/character_repositories/character_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities import Character


class ICharacterRepository(ABC):

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