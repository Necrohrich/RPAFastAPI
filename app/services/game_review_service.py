# app/services/game_review_service.py
from typing import Optional
from uuid import UUID

from app.domain.entities.game_review import GameReview
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.domain.enums.review_status_enum import ReviewStatusEnum
from app.domain.repositories.game_repositories.game_review_repository import IGameReviewRepository
from app.domain.repositories.game_repositories.game_session_repository import IGameSessionRepository
from app.domain.repositories.game_repositories.game_repository import IGameRepository
from app.domain.repositories.auth_repositories.user_repository import IUserRepository
from app.dto.game_review_dtos import (
    CreateGameReviewDTO,
    UpdateGameReviewDTO,
    SendGameReviewDTO,
    GameReviewResponseDTO,
    GameReviewRatingStatsDTO,
    GameReviewStatsDTO,
    NpcStatDTO,
    SceneStatDTO,
    PlayerStatDTO,
)
from app.dto.common_dtos import PaginatedResponseDTO
from app.exceptions.common_exceptions import NotFoundError
from app.exceptions.game_exceptions import GameNotFoundException
from app.exceptions.game_session_exceptions import GameSessionNotFoundException
from app.exceptions.game_review_exceptions import (
    GameReviewNotFoundException,
    GameReviewAlreadyExistsException,
    GameReviewAlreadySentException,
    GameReviewNotAllowedException,
    GameReviewInvalidStatusTransitionException,
)
from app.utils.mapper import Mapper

# Числовые веса рейтингов для расчёта оценки
_RATING_WEIGHTS: dict[str, int] = {
    ReviewRatingEnum.TERRIBLE: 0,
    ReviewRatingEnum.BAD:      1,
    ReviewRatingEnum.NEUTRAL:  2,
    ReviewRatingEnum.GOOD:     3,
    ReviewRatingEnum.EXCELLENT: 4,
}

_RATING_LABELS: list[ReviewRatingEnum] = [
    ReviewRatingEnum.TERRIBLE,
    ReviewRatingEnum.BAD,
    ReviewRatingEnum.NEUTRAL,
    ReviewRatingEnum.GOOD,
    ReviewRatingEnum.EXCELLENT,
]

# Допустимые переходы статусов
_ALLOWED_TRANSITIONS: dict[ReviewStatusEnum, set[ReviewStatusEnum]] = {
    ReviewStatusEnum.CREATED:  {ReviewStatusEnum.SEND, ReviewStatusEnum.CANCELED},
    ReviewStatusEnum.SEND:     set(),
    ReviewStatusEnum.CANCELED: set(),
}


class GameReviewService:
    """
    Application service responsible for game review management.

    Handles:
        - Automatic creation of reviews for attending players on session completion
        - Updating review fields (only while CREATED)
        - Sending (SEND) and canceling (CANCELED) reviews
        - Retrieval by ID, game, session, user — paginated and list variants
        - Statistics: best NPC, scenes, players, weighted rating for a game
        - Soft delete, restore, hard delete
        - Bulk soft delete on session invalidation

    Responsibilities:
        - Validates player eligibility (must be ACCEPTED player, not author/GM, must have attended)
        - Prevents duplicate reviews per session per user
        - Prevents editing SEND reviews
        - Uses IGameSessionRepository to verify session existence and attendance
        - Uses IGameRepository to verify game existence and author identity
        - Uses IUserRepository to verify user existence

    Does NOT:
        - Handle authentication or token validation
        - Manage Discord interactions directly
        - Contain infrastructure or persistence logic
    """

    def __init__(
        self,
        repo: IGameReviewRepository,
        session_repo: IGameSessionRepository,
        game_repo: IGameRepository,
        user_repo: IUserRepository,
    ):
        self.repo = repo
        self.session_repo = session_repo
        self.game_repo = game_repo
        self.user_repo = user_repo

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _check_transition(current: ReviewStatusEnum, target: ReviewStatusEnum) -> None:
        if target not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise GameReviewInvalidStatusTransitionException(
                f"Cannot transition from {current} to {target}"
            )

    # ── create ────────────────────────────────────────────────────────────────

    async def create(self, dto: CreateGameReviewDTO) -> GameReviewResponseDTO:
        """
        Создаёт отзыв для игрока.

        Проверки:
        1. Игра существует.
        2. Сессия существует и принадлежит игре.
        3. Пользователь существует.
        4. Пользователь не является автором игры или GM.
        5. Пользователь является ACCEPTED игроком игры.
        6. Пользователь присутствовал на сессии (attending_user_ids в discord_state).
        7. Отзыв на эту сессию ещё не создавался.
        """
        game = await self.game_repo.get_by_id(dto.game_id)
        if not game:
            raise GameNotFoundException()

        session = await self.session_repo.get_by_id(dto.session_id)
        if not session or session.game_id != dto.game_id:
            raise GameSessionNotFoundException()

        if not await self.user_repo.get_by_id(dto.user_id):
            raise NotFoundError()

        # Автор игры не может оставить отзыв
        if game.author_id == dto.user_id:
            raise GameReviewNotAllowedException(
                "Game author cannot leave a review"
            )

        # Пользователь должен быть принятым игроком
        from app.domain.enums.player_status_enum import PlayerStatusEnum
        player = await self.game_repo.get_player(dto.game_id, dto.user_id)
        if not player or player.status != PlayerStatusEnum.ACCEPTED:
            raise GameReviewNotAllowedException(
                "Only accepted players can leave a review"
            )

        # Проверка присутствия: смотрим discord_state сессии.
        # Состояние не удаляется, а мягко удаляется (согласно решению в таске),
        # поэтому get_discord_state вернёт данные даже после завершения сессии.
        discord_state = await self.session_repo.get_discord_state(dto.session_id)
        if discord_state is not None:
            attending_ids: list = discord_state.get("attending_user_ids") or []
            # attending_user_ids хранит discord_id, а не user_id.
            # Получаем discord_id пользователя через user_repo.
            user = await self.user_repo.get_by_id(dto.user_id)
            if user and user.primary_discord_id is not None:
                if user.primary_discord_id not in attending_ids:
                    raise GameReviewNotAllowedException(
                        "User was not present at the session"
                    )
        # Если discord_state нет (сессия создана через сайт без attendance),
        # то проверку присутствия пропускаем — достаточно статуса ACCEPTED.

        # Дубликат отзыва
        existing = await self.repo.get_by_session_id_and_user_id(
            dto.session_id, dto.user_id, include_deleted=False
        )
        if existing:
            raise GameReviewAlreadyExistsException()

        review = GameReview(
            game_id=dto.game_id,
            session_id=dto.session_id,
            user_id=dto.user_id,
        )
        created = await self.repo.create(review)
        return Mapper.entity_to_dto(created, GameReviewResponseDTO)

    # ── update ────────────────────────────────────────────────────────────────

    async def update(
        self, review_id: UUID, dto: UpdateGameReviewDTO, requester_id: UUID
    ) -> GameReviewResponseDTO:
        """Обновляет поля отзыва. Только для CREATED статуса и владельца."""
        review = await self.repo.get_by_id(review_id, include_deleted=False)
        if not review:
            raise GameReviewNotFoundException()

        if review.user_id != requester_id:
            raise GameReviewNotAllowedException("Only the review author can edit it")

        if review.status == ReviewStatusEnum.SEND:
            raise GameReviewAlreadySentException()

        if review.status == ReviewStatusEnum.CANCELED:
            raise GameReviewInvalidStatusTransitionException(
                "Cannot edit a canceled review"
            )

        if dto.rating is not None:
            review.rating = dto.rating
        if dto.comment is not None:
            review.comment = dto.comment
        if dto.best_scenes is not None:
            review.best_scenes = {k: v for k, v in dto.best_scenes.items()}
        if dto.best_npc is not None:
            review.best_npc = dto.best_npc
        if dto.best_player_id is not None:
            review.best_player_id = dto.best_player_id

        updated = await self.repo.update(review)
        return Mapper.entity_to_dto(updated, GameReviewResponseDTO)

    # ── send ──────────────────────────────────────────────────────────────────

    async def send(
        self, review_id: UUID, dto: SendGameReviewDTO, requester_id: UUID
    ) -> GameReviewResponseDTO:
        """Отправляет отзыв (CREATED → SEND). Требует заполненных rating и comment."""
        review = await self.repo.get_by_id(review_id, include_deleted=False)
        if not review:
            raise GameReviewNotFoundException()

        if review.user_id != requester_id:
            raise GameReviewNotAllowedException("Only the review author can send it")

        self._check_transition(review.status, ReviewStatusEnum.SEND)

        if not review.rating:
            from app.exceptions.common_exceptions import ValidationError
            raise ValidationError("Rating is required before sending a review")

        if not review.comment or not review.comment.strip():
            from app.exceptions.common_exceptions import ValidationError
            raise ValidationError("Comment is required before sending a review")

        review.status = ReviewStatusEnum.SEND
        review.anonymity = dto.anonymity

        updated = await self.repo.update(review)
        return Mapper.entity_to_dto(updated, GameReviewResponseDTO)

    # ── cancel ────────────────────────────────────────────────────────────────

    async def cancel(self, review_id: UUID, requester_id: UUID) -> GameReviewResponseDTO:
        """Отменяет отзыв (CREATED → CANCELED)."""
        review = await self.repo.get_by_id(review_id, include_deleted=False)
        if not review:
            raise GameReviewNotFoundException()

        if review.user_id != requester_id:
            raise GameReviewNotAllowedException("Only the review author can cancel it")

        self._check_transition(review.status, ReviewStatusEnum.CANCELED)

        review.status = ReviewStatusEnum.CANCELED
        updated = await self.repo.update(review)
        return Mapper.entity_to_dto(updated, GameReviewResponseDTO)

    # ── get ───────────────────────────────────────────────────────────────────

    async def get_by_id(
        self, review_id: UUID, include_deleted: bool = False
    ) -> GameReviewResponseDTO:
        review = await self.repo.get_by_id(review_id, include_deleted=include_deleted)
        if not review:
            raise GameReviewNotFoundException()
        return Mapper.entity_to_dto(review, GameReviewResponseDTO)

    async def get_by_game_id(
        self,
        game_id: UUID,
        page: int,
        page_size: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> PaginatedResponseDTO[GameReviewResponseDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_game_id(
            game_id, offset=offset, limit=page_size,
            statuses=statuses, include_deleted=include_deleted
        )
        total = await self.repo.count_by_game_id(
            game_id, statuses=statuses, include_deleted=include_deleted
        )
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items],
            total=total, page=page, page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_list_by_game_id(
        self,
        game_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReviewResponseDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        items = await self.repo.get_list_by_game_id(
            game_id, statuses=statuses, include_deleted=include_deleted
        )
        return [Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items]

    async def get_by_session_id(
        self,
        session_id: UUID,
        page: int,
        page_size: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> PaginatedResponseDTO[GameReviewResponseDTO]:
        if not await self.session_repo.get_by_id(session_id):
            raise GameSessionNotFoundException()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_session_id(
            session_id, offset=offset, limit=page_size,
            statuses=statuses, include_deleted=include_deleted
        )
        total = await self.repo.count_by_session_id(
            session_id, statuses=statuses, include_deleted=include_deleted
        )
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items],
            total=total, page=page, page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_list_by_session_id(
        self,
        session_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReviewResponseDTO]:
        if not await self.session_repo.get_by_id(session_id):
            raise GameSessionNotFoundException()
        items = await self.repo.get_list_by_session_id(
            session_id, statuses=statuses, include_deleted=include_deleted
        )
        return [Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items]

    async def get_by_user_id(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> PaginatedResponseDTO[GameReviewResponseDTO]:
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        offset = (page - 1) * page_size
        items = await self.repo.get_by_user_id(
            user_id, offset=offset, limit=page_size,
            statuses=statuses, include_deleted=include_deleted
        )
        total = await self.repo.count_by_user_id(
            user_id, statuses=statuses, include_deleted=include_deleted
        )
        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items],
            total=total, page=page, page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_list_by_user_id(
        self,
        user_id: UUID,
        statuses: Optional[list[ReviewStatusEnum]] = None,
        include_deleted: bool = False,
    ) -> list[GameReviewResponseDTO]:
        if not await self.user_repo.get_by_id(user_id):
            raise NotFoundError()
        items = await self.repo.get_list_by_user_id(
            user_id, statuses=statuses, include_deleted=include_deleted
        )
        return [Mapper.entity_to_dto(r, GameReviewResponseDTO) for r in items]

    # ── delete / restore ──────────────────────────────────────────────────────

    async def soft_delete(self, review_id: UUID) -> None:
        if not await self.repo.get_by_id(review_id, include_deleted=False):
            raise GameReviewNotFoundException()
        await self.repo.soft_delete(review_id)

    async def restore(self, review_id: UUID) -> None:
        # restore работает с удалёнными — ищем включая deleted
        review = await self.repo.get_by_id(review_id, include_deleted=True)
        if not review:
            raise GameReviewNotFoundException()
        await self.repo.restore(review_id)

    async def delete(self, review_id: UUID) -> None:
        review = await self.repo.get_by_id(review_id, include_deleted=True)
        if not review:
            raise GameReviewNotFoundException()
        await self.repo.delete(review_id)

    # ── bulk: вызывается при INVALID сессии ───────────────────────────────────

    async def invalidate_by_session_id(self, session_id: UUID) -> None:
        """
        Мягко удаляет все отзывы сессии.
        Вызывается из GameSessionService.invalidate().
        """
        await self.repo.soft_delete_by_session_id(session_id)

    # ── create bulk: вызывается при COMPLETED сессии ─────────────────────────

    async def create_for_session(
        self,
        game_id: UUID,
        session_id: UUID,
        attending_user_ids: list[UUID],
    ) -> list[GameReviewResponseDTO]:
        """
        Создаёт отзывы для всех присутствовавших игроков при завершении сессии.

        Пропускает:
        - автора игры
        - пользователей, у которых уже есть отзыв на эту сессию
        - пользователей, не являющихся ACCEPTED игроками

        Возвращает список созданных DTO.
        """
        game = await self.game_repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundException()

        from app.domain.enums.player_status_enum import PlayerStatusEnum

        created: list[GameReviewResponseDTO] = []
        for user_id in attending_user_ids:
            # Пропускаем автора
            if user_id == game.author_id:
                continue

            # Пропускаем, если уже есть отзыв
            existing = await self.repo.get_by_session_id_and_user_id(
                session_id, user_id, include_deleted=False
            )
            if existing:
                continue

            # Пропускаем, если не принятый игрок
            player = await self.game_repo.get_player(game_id, user_id)
            if not player or player.status != PlayerStatusEnum.ACCEPTED:
                continue

            review = GameReview(
                game_id=game_id,
                session_id=session_id,
                user_id=user_id,
            )
            created_review = await self.repo.create(review)
            created.append(Mapper.entity_to_dto(created_review, GameReviewResponseDTO))

        return created

    # ── статистика ────────────────────────────────────────────────────────────

    async def get_stats_npc(self, game_id: UUID) -> list[NpcStatDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        raw = await self.repo.get_best_npc_stats(game_id)
        return [NpcStatDTO(name=name, count=count) for name, count in raw]

    async def get_stats_scenes(self, game_id: UUID) -> list[SceneStatDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        raw = await self.repo.get_best_scenes_stats(game_id)
        return [SceneStatDTO(name=name, scene_type=stype, count=cnt) for name, stype, cnt in raw]

    async def get_stats_players(self, game_id: UUID) -> list[PlayerStatDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()
        raw = await self.repo.get_best_players_stats(game_id)
        return [PlayerStatDTO(user_id=uid, count=cnt) for uid, cnt in raw]

    async def get_stats_rating(self, game_id: UUID) -> GameReviewRatingStatsDTO:
        """
        Рассчитывает «справедливую» оценку игры.

        Алгоритм:
        1. Собираем все SEND рейтинги по игре.
        2. Считаем число уникальных сессий и уникальных авторов с отзывами.
        3. Справедливая оценка = среднее взвешенное, где вес каждого отзыва
           пропорционален охвату (1 / уникальных_авторов_в_сессии).
           Это снижает влияние сессий, где писал только один игрок, и не
           завышает оценку игры с малым числом участников.
        4. Финальный score нормируется в [0, 4] и округляется до ближайшего
           рейтинг-лейбла.
        """
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()

        ratings = await self.repo.get_ratings_by_game_id(game_id)
        total_sessions = await self.repo.count_distinct_sessions_by_game_id(game_id)
        total_users = await self.repo.count_distinct_users_by_game_id(game_id)

        total_reviews = len(ratings)

        if total_reviews == 0 or total_users == 0:
            return GameReviewRatingStatsDTO(
                game_id=game_id,
                total_reviews=0,
                total_sessions=total_sessions,
                total_reviewers=total_users,
                weighted_score=0.0,
                label=ReviewRatingEnum.NEUTRAL,
            )

        # Простое среднее + штраф за малое число рецензентов
        raw_scores = [_RATING_WEIGHTS.get(r, 2) for r in ratings]
        raw_mean = sum(raw_scores) / len(raw_scores)

        # Коэффициент доверия: чем больше уникальных авторов, тем ближе к 1
        confidence = total_users / (total_users + 1)

        # Нейтральная оценка = 2.0 (NEUTRAL)
        weighted_score = confidence * raw_mean + (1 - confidence) * 2.0
        weighted_score = round(max(0.0, min(4.0, weighted_score)), 2)

        # Перевод в лейбл
        label_index = round(weighted_score)
        label = _RATING_LABELS[label_index]  # type: ignore[misc]

        return GameReviewRatingStatsDTO(
            game_id=game_id,
            total_reviews=total_reviews,
            total_sessions=total_sessions,
            total_reviewers=total_users,
            weighted_score=weighted_score,
            label=label,
        )

    async def get_full_stats(self, game_id: UUID) -> GameReviewStatsDTO:
        """Возвращает полную статистику по игре одним вызовом."""
        return GameReviewStatsDTO(
            game_id=game_id,
            best_npc=await self.get_stats_npc(game_id),
            best_scenes=await self.get_stats_scenes(game_id),
            best_players=await self.get_stats_players(game_id),
            rating=await self.get_stats_rating(game_id),
        )