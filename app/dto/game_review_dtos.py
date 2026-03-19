# app/dto/game_review_dtos.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.domain.enums.review_scene_type_enum import ReviewSceneTypeEnum
from app.domain.enums.review_status_enum import ReviewStatusEnum


class CreateGameReviewDTO(BaseModel):
    """Создание отзыва. Используется внутри сервиса, не через роутер напрямую."""
    model_config = ConfigDict(extra="forbid")

    game_id: UUID
    session_id: UUID
    user_id: UUID


class UpdateGameReviewDTO(BaseModel):
    """Обновление полей отзыва (только пока статус CREATED)."""
    model_config = ConfigDict(extra="forbid")

    rating: Optional[ReviewRatingEnum] = None
    comment: Optional[str] = None
    # {название сцены: тип сцены}
    best_scenes: Optional[dict[str, ReviewSceneTypeEnum]] = None
    best_npc: Optional[list[str]] = None
    best_player_id: Optional[UUID] = None


class SendGameReviewDTO(BaseModel):
    """Отправка отзыва с выбором анонимности."""
    model_config = ConfigDict(extra="forbid")

    anonymity: ReviewAnonymityEnum = ReviewAnonymityEnum.PUBLIC


class GameReviewResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    game_id: UUID
    session_id: UUID
    user_id: UUID
    status: ReviewStatusEnum
    anonymity: ReviewAnonymityEnum
    rating: Optional[ReviewRatingEnum] = None
    comment: str = ""
    best_scenes: Optional[dict] = None
    best_npc: Optional[list] = None
    best_player_id: Optional[UUID] = None


# ── Статистика ────────────────────────────────────────────────────────────────

class NpcStatDTO(BaseModel):
    name: str
    count: int


class SceneStatDTO(BaseModel):
    name: str
    scene_type: str
    count: int


class PlayerStatDTO(BaseModel):
    user_id: UUID
    count: int


class GameReviewRatingStatsDTO(BaseModel):
    """Результат расчёта справедливой оценки игры."""
    game_id: UUID
    # Число SEND отзывов, использованных в расчёте
    total_reviews: int
    # Число уникальных сессий с хотя бы одним отзывом
    total_sessions: int
    # Число уникальных авторов отзывов
    total_reviewers: int
    # Средневзвешенная оценка (0.0–4.0, где 0=TERRIBLE, 4=EXCELLENT)
    weighted_score: float
    # Понятный лейбл: TERRIBLE / BAD / NEUTRAL / GOOD / EXCELLENT
    label: str


class GameReviewStatsDTO(BaseModel):
    """Полная статистика по игре."""
    game_id: UUID
    best_npc: list[NpcStatDTO]
    best_scenes: list[SceneStatDTO]
    best_players: list[PlayerStatDTO]
    rating: GameReviewRatingStatsDTO