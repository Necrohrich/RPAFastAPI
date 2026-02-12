#app/domain/entities/user.py

from dataclasses import dataclass
from uuid import UUID
from app.domain.entities.base_entity import BaseEntity

@dataclass(kw_only=True)
class User(BaseEntity):
    """
    Domain Entity representing user.

    Attributes:
        email (str): Email пользователя. Site-only.
        password_hash (str): Пароль пользователя. Site-only.
        discord_id (int): Discord User ID.
        joined_from (UUID): Указывает идентификатор User, с которого перенесены данные.
        joined_to (UUID): Указывает идентификатор User, на который перенесены данные.

    Warning:
        - Сайт и Discord могут на своей стороне создать сущности User, которые не будут
        знать друг о друге. joined_from и joined_to будут хранить историю слияния двух сущностей.
    """

    email: str = ""
    password_hash: str = ""
    discord_id: int | None = None
    joined_from: UUID | None = None
    joined_to: UUID | None = None



