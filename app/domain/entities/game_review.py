# app/domain/entities/game_review.py
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity
from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.domain.enums.review_scene_type_enum import ReviewSceneTypeEnum
from app.domain.enums.review_status_enum import ReviewStatusEnum

@dataclass(kw_only=True)
class GameReview(BaseEntity):
    """
    Domain Entity representing a game review (игровой отзыв).

    Создаётся автоматически при переходе GameSession в COMPLETED
    для каждого присутствовавшего игрока.

    Attributes:
        game_id (UUID):       Привязка к игре.
        session_id (UUID):    Привязка к игровой сессии.
        user_id (UUID):       Игрок, оставляющий отзыв.
        status (ReviewStatusEnum): CREATED → SEND | CANCELED.
        anonymity (ReviewAnonymityEnum): PUBLIC или PRIVATE.
        rating (ReviewRatingEnum | None): Оценка впечатления от сессии.
        comment (str):        Текстовый комментарий.
        best_scenes (dict):   {название сцены: ReviewSceneTypeEnum}.
        best_npc (list[str]): Имена запомнившихся НИП.
        best_player_id (UUID | None): user_id лучшего игрока сессии.
    """
    game_id:    UUID
    session_id: UUID
    user_id:    UUID

    status:    ReviewStatusEnum   = ReviewStatusEnum.CREATED
    anonymity: ReviewAnonymityEnum = ReviewAnonymityEnum.PUBLIC

    rating:  Optional[ReviewRatingEnum] = None
    comment: str = ""

    best_scenes: dict[str, ReviewSceneTypeEnum] = field(default_factory=dict)
    best_npc: list[str] = field(default_factory=list)
    best_player_id: Optional[UUID] = None