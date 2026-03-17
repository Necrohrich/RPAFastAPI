# app/services/game_session_service.py
from uuid import UUID

from app.domain.entities import GameSession
from app.domain.enums import GameSessionStatusEnum
from app.domain.repositories import IGameSessionRepository, IGameRepository
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO, GameSessionResponseDTO, PaginatedResponseDTO
from app.exceptions import (
    GameNotFoundException,
    GameSessionNotFoundException,
    GameSessionAlreadyActiveException,
    GameSessionInvalidStatusTransitionException,
)
from app.utils import Mapper

# Допустимые переходы статусов: {текущий: {допустимые следующие}}
_ALLOWED_TRANSITIONS: dict[GameSessionStatusEnum, set[GameSessionStatusEnum]] = {
    GameSessionStatusEnum.CREATED:   {GameSessionStatusEnum.ACTIVE, GameSessionStatusEnum.CANCELED, GameSessionStatusEnum.INVALID},
    GameSessionStatusEnum.ACTIVE:    {GameSessionStatusEnum.COMPLETED, GameSessionStatusEnum.CANCELED, GameSessionStatusEnum.INVALID},
    GameSessionStatusEnum.COMPLETED: {GameSessionStatusEnum.INVALID},
    GameSessionStatusEnum.CANCELED:  {GameSessionStatusEnum.INVALID},
    GameSessionStatusEnum.INVALID:   set(),
}


class GameSessionService:
    """
    Application service responsible for game session lifecycle management.

    Handles:
        - Session creation with automatic session_number assignment
        - Retrieval by ID, by game (paginated), by Discord event ID
        - Updating content fields (title, description, image_url, started_at, ended_at)
        - Status transitions: start, complete, cancel, invalidate
        - Enforcement of the single-active-session-per-game rule

    Responsibilities:
        - Uses IGameSessionRepository as primary data source
        - Uses IGameRepository to verify game existence
        - Enforces status transition rules via _check_transition()
        - Delegates active-session collision detection to the repository

    Does NOT:
        - Handle authentication or token validation
        - Manage Discord Scheduled Events directly (delegated to Discord layer)
        - Enforce role-based access (delegated to router/Discord layer)
        - Contain infrastructure or persistence logic
    """

    def __init__(
        self,
        repo: IGameSessionRepository,
        game_repo: IGameRepository,
    ):
        self.repo = repo
        self.game_repo = game_repo

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_transition(
        current: GameSessionStatusEnum,
        target: GameSessionStatusEnum,
    ) -> None:
        """Бросает исключение, если переход статуса недопустим."""
        if target not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise GameSessionInvalidStatusTransitionException(
                f"Cannot transition from {current} to {target}"
            )

    async def _get_or_raise(self, session_id: UUID) -> GameSession:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise GameSessionNotFoundException()
        return session

    # ── write ─────────────────────────────────────────────────────────────────

    async def create(self, dto: CreateGameSessionDTO) -> GameSessionResponseDTO:
        """Создаёт новую сессию со статусом CREATED и следующим порядковым номером.

        Проверяет существование игры. Нумерация ведётся только по действительным
        сессиям (не CANCELED / INVALID).
        """
        if not await self.game_repo.get_by_id(dto.game_id):
            raise GameNotFoundException()

        session_number = await self.repo.get_next_session_number(dto.game_id)

        session = GameSession(
            game_id=dto.game_id,
            session_number=session_number,
            discord_event_id=dto.discord_event_id,
            title=dto.title or "",
            description=dto.description or "",
            image_url=dto.image_url or "",
            status=GameSessionStatusEnum.CREATED,
        )

        created = await self.repo.create(session)
        return Mapper.entity_to_dto(created, GameSessionResponseDTO)

    async def update(
        self,
        session_id: UUID,
        dto: UpdateGameSessionDTO,
    ) -> GameSessionResponseDTO:
        """Обновляет контентные поля сессии (title, description, image_url, даты).

        Статус через этот метод не меняется — для этого есть start/complete/cancel/invalidate.
        """
        session = await self._get_or_raise(session_id)

        if dto.title is not None:
            session.title = dto.title
        if dto.description is not None:
            session.description = dto.description
        if dto.image_url is not None:
            session.image_url = dto.image_url
        if dto.started_at is not None:
            session.started_at = dto.started_at
        if dto.ended_at is not None:
            session.ended_at = dto.ended_at

        updated = await self.repo.update(session)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def start(self, session_id: UUID) -> GameSessionResponseDTO:
        """Переводит сессию в статус ACTIVE.

        Перед переходом проверяет, что для данной игры нет другой ACTIVE-сессии.
        Если есть — бросает GameSessionAlreadyActiveException.
        """
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.ACTIVE)

        existing_active = await self.repo.get_active_by_game_id(session.game_id)
        if existing_active and existing_active.id != session_id:
            raise GameSessionAlreadyActiveException()

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.ACTIVE)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def complete(self, session_id: UUID) -> GameSessionResponseDTO:
        """Переводит сессию в статус COMPLETED."""
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.COMPLETED)

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.COMPLETED)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def cancel(self, session_id: UUID) -> GameSessionResponseDTO:
        """Переводит сессию в статус CANCELED.

        Может выполнить автор игры или администратор.
        Отменённые сессии не учитываются в нумерации.
        """
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.CANCELED)

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.CANCELED)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def invalidate(self, session_id: UUID) -> GameSessionResponseDTO:
        """Переводит сессию в статус INVALID.

        Доступно только MODERATOR и выше (проверка прав — на стороне роутера).
        Помечает сессию недействительной (тестовая, ошибочно созданная и т.п.).
        """
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.INVALID)

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.INVALID)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    # ── read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, session_id: UUID) -> GameSessionResponseDTO:
        session = await self._get_or_raise(session_id)
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_by_game_id(
        self,
        game_id: UUID,
        page: int,
        page_size: int,
    ) -> PaginatedResponseDTO[GameSessionResponseDTO]:
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()

        offset = (page - 1) * page_size
        items = await self.repo.get_by_game_id(game_id, offset=offset, limit=page_size)
        total = await self.repo.count_by_game_id(game_id)

        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(s, GameSessionResponseDTO) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_active_by_game_id(self, game_id: UUID) -> GameSessionResponseDTO:
        """Возвращает активную сессию игры или бросает исключение, если её нет."""
        session = await self.repo.get_active_by_game_id(game_id)
        if not session:
            raise GameSessionNotFoundException()
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_by_discord_event_id(
        self,
        discord_event_id: int,
    ) -> GameSessionResponseDTO:
        """Возвращает сессию по ID Discord Scheduled Event."""
        session = await self.repo.get_by_discord_event_id(discord_event_id)
        if not session:
            raise GameSessionNotFoundException()
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)