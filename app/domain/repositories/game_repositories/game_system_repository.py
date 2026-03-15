# app/domain/repositories/game_repositories/game_system_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import GameSystem


class IGameSystemRepository(ABC):
    """
    Интерфейс репозитория для работы с игровыми системами.

    Управляет CRUD операциями справочника игровых систем (D&D 5e, GURPS и др.).

    Методы:
        * create — создаёт новую игровую систему и возвращает её с присвоенным ID
        * get_by_id — возвращает игровую систему по UUID
        * get_by_name — возвращает игровую систему по уникальному названию
        * get_all — возвращает список всех игровых систем без фильтрации
        * count_all — возвращает число игровых систем
        * update — обновляет поля игровой системы и возвращает обновлённую сущность
        * delete — физически удаляет игровую систему по UUID
        * has_dependencies — указывает, есть ли зависимости у игровой системы
    """

    @abstractmethod
    async def create(self, game_system: GameSystem) -> GameSystem: ...

    @abstractmethod
    async def get_by_id(self, game_system_id: UUID) -> Optional[GameSystem]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[GameSystem]: ...

    @abstractmethod
    async def get_all(self, offset: int, limit: int) -> list[GameSystem]: ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def update(self, game_system: GameSystem) -> GameSystem: ...

    @abstractmethod
    async def delete(self, game_system_id: UUID) -> None: ...

    @abstractmethod
    async def has_dependencies(self, game_system_id: UUID) -> bool: ...