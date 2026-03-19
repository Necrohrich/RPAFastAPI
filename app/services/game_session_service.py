# app/services/game_session_service.py
from typing import Optional
from uuid import UUID

from app.domain.entities import GameSession, Game
from app.domain.enums import GameSessionStatusEnum
from app.domain.repositories import IGameSessionRepository, IGameRepository
from app.domain.repositories.game_repositories.game_review_repository import IGameReviewRepository
from app.dto import CreateGameSessionDTO, UpdateGameSessionDTO, GameSessionResponseDTO, PaginatedResponseDTO
from app.exceptions import (
    GameNotFoundException,
    GameSessionNotFoundException,
    GameSessionAlreadyActiveException,
    GameSessionInvalidStatusTransitionException,
)
from app.exceptions import (
    SessionAlreadyLinkedToEventException,
    EventAlreadyLinkedToSessionException,
)
from app.utils import Mapper

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
        - Retrieval by ID, by game (all or completed only, paginated), by Discord event ID
        - Updating content fields (title, description, image_url, started_at, ended_at)
        - Status transitions: start, complete, cancel, invalidate
        - Enforcement of the single-active-session-per-game rule
        - Linking Discord Scheduled Events to sessions manually (/session link)
        - Creating/deleting Discord states on start/complete/cancel/invalidate
        - Discord-layer helpers: session/game lookup by event, discord_state access,
          accepted players and character names for session roles
        - On invalidate: soft-deletes all related game reviews via IGameReviewRepository

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
        review_repo: Optional[IGameReviewRepository] = None,
    ):
        self.repo = repo
        self.game_repo = game_repo
        self.review_repo = review_repo

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_transition(current: GameSessionStatusEnum, target: GameSessionStatusEnum) -> None:
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

    async def update(self, session_id: UUID, dto: UpdateGameSessionDTO) -> GameSessionResponseDTO:
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

    async def start(
        self,
        session_id: UUID,
        attending_user_ids: Optional[list[int]] = None,
        attendance_message_id=None
    ) -> GameSessionResponseDTO:
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.ACTIVE)

        existing_active = await self.repo.get_active_by_game_id(session.game_id)
        if existing_active and existing_active.id != session_id:
            raise GameSessionAlreadyActiveException()

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.ACTIVE)
        await self.repo.create_discord_state(
            session_id=session_id,
            attending_user_ids=attending_user_ids or [],
            attendance_message_id=attendance_message_id,
        )
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def complete(self, session_id: UUID) -> GameSessionResponseDTO:
        """Переводит сессию в COMPLETED. Discord-состояние НЕ удаляется —
        оно нужно для системы отзывов (attending_user_ids).
        Физическое удаление состояния перенесено в отдельный метод cleanup_discord_state."""
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.COMPLETED)

        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.COMPLETED)
        # Не удаляем discord_state — система отзывов читает attending_user_ids из него.
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    async def cancel(self, session_id: UUID) -> tuple[GameSessionResponseDTO, Optional[dict]]:
        """Переводит сессию в CANCELED, возвращает DTO и discord_state до его удаления."""
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.CANCELED)

        discord_state = await self.repo.get_discord_state(session_id)
        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.CANCELED)
        await self.repo.delete_discord_state(session_id)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO), discord_state

    async def invalidate(self, session_id: UUID) -> tuple[GameSessionResponseDTO, Optional[dict]]:
        """
        Переводит сессию в INVALID, возвращает DTO и discord_state до его удаления.

        Дополнительно: мягко удаляет все связанные отзывы (если review_repo передан).
        """
        session = await self._get_or_raise(session_id)
        self._check_transition(session.status, GameSessionStatusEnum.INVALID)

        discord_state = await self.repo.get_discord_state(session_id)
        updated = await self.repo.update_status(session_id, GameSessionStatusEnum.INVALID)
        await self.repo.delete_discord_state(session_id)

        # Мягко удаляем все отзывы этой сессии
        if self.review_repo is not None:
            await self.review_repo.soft_delete_by_session_id(session_id)

        return Mapper.entity_to_dto(updated, GameSessionResponseDTO), discord_state

    async def link_discord_event(
        self, session_id: UUID, discord_event_id: int,
    ) -> GameSessionResponseDTO:
        """Привязывает Discord Scheduled Event к сессии вручную (SUPPORT+)."""
        session = await self._get_or_raise(session_id)

        if session.discord_event_id and session.discord_event_id != discord_event_id:
            raise SessionAlreadyLinkedToEventException()

        existing = await self.repo.get_by_discord_event_id(discord_event_id)
        if existing and existing.id != session_id:
            raise EventAlreadyLinkedToSessionException()

        updated = await self.repo.link_discord_event(session_id, discord_event_id)
        return Mapper.entity_to_dto(updated, GameSessionResponseDTO)

    # ── read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, session_id: UUID) -> GameSessionResponseDTO:
        session = await self._get_or_raise(session_id)
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_by_game_id(
        self, game_id: UUID, page: int, page_size: int,
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

    async def get_completed_by_game_id(
        self,
        game_id: UUID,
        page: int,
        page_size: int,
        from_number: Optional[int] = None,
        to_number: Optional[int] = None,
    ) -> PaginatedResponseDTO[GameSessionResponseDTO]:
        """Завершённые сессии с опциональной фильтрацией по диапазону номеров."""
        if not await self.game_repo.get_by_id(game_id):
            raise GameNotFoundException()

        offset = (page - 1) * page_size
        items = await self.repo.get_completed_by_game_id(
            game_id, offset=offset, limit=page_size,
            from_number=from_number, to_number=to_number,
        )
        total = await self.repo.count_completed_by_game_id(
            game_id, from_number=from_number, to_number=to_number,
        )

        return PaginatedResponseDTO(
            items=[Mapper.entity_to_dto(s, GameSessionResponseDTO) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_active_by_game_id(self, game_id: UUID) -> GameSessionResponseDTO:
        session = await self.repo.get_active_by_game_id(game_id)
        if not session:
            raise GameSessionNotFoundException()
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def find_active_by_game_id(self, game_id: UUID) -> Optional[GameSessionResponseDTO]:
        """Возвращает активную сессию или None. Для случаев, где отсутствие сессии — норма."""
        session = await self.repo.get_active_by_game_id(game_id)
        if not session:
            return None
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_by_discord_event_id(self, discord_event_id: int) -> GameSessionResponseDTO:
        """Возвращает сессию по event_id. Бросает исключение если не найдена."""
        session = await self.repo.get_by_discord_event_id(discord_event_id)
        if not session:
            raise GameSessionNotFoundException()
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_last_valid_by_game_id(self, game_id: UUID) -> Optional[GameSessionResponseDTO]:
        """Последняя действительная сессия игры (не CANCELED/INVALID). Для /session info."""
        session = await self.repo.get_last_valid_by_game_id(game_id)
        if not session:
            return None
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def get_created_list_by_author_discord_id(self, discord_id: int) -> list[GameSessionResponseDTO]:
        """CREATED-сессии игр пользователя. Используется в /session link."""
        games = await self.game_repo.get_list_by_author_discord_id(discord_id)
        result: list[GameSessionResponseDTO] = []
        for game in games:
            sessions = await self.repo.get_by_game_id_and_statuses(
                game.id,
                statuses=[GameSessionStatusEnum.CREATED],
            )
            result.extend(Mapper.entity_to_dto(s, GameSessionResponseDTO) for s in sessions)
        return result

    async def get_active_or_created_list_by_author_discord_id(self, discord_id: int) -> list[GameSessionResponseDTO]:
        """ACTIVE + CREATED сессии игр пользователя. Используется в /session cancel."""
        games = await self.game_repo.get_list_by_author_discord_id(discord_id)
        result: list[GameSessionResponseDTO] = []
        for game in games:
            sessions = await self.repo.get_by_game_id_and_statuses(
                game.id,
                statuses=[GameSessionStatusEnum.CREATED, GameSessionStatusEnum.ACTIVE],
            )
            result.extend(Mapper.entity_to_dto(s, GameSessionResponseDTO) for s in sessions)
        return result

    async def get_non_invalid_list(self) -> list[GameSessionResponseDTO]:
        """Все сессии кроме INVALID. Используется в /session invalidate (MODERATOR+)."""
        sessions = await self.repo.get_by_statuses(
            statuses=[
                GameSessionStatusEnum.CREATED,
                GameSessionStatusEnum.ACTIVE,
                GameSessionStatusEnum.COMPLETED,
                GameSessionStatusEnum.CANCELED,
            ]
        )
        return [Mapper.entity_to_dto(s, GameSessionResponseDTO) for s in sessions]

    # ── discord helpers ───────────────────────────────────────────────────────

    async def get_session_by_event_id(self, discord_event_id: int) -> Optional[GameSessionResponseDTO]:
        """Возвращает сессию по event_id или None. Для слушателей событий."""
        session = await self.repo.get_by_discord_event_id(discord_event_id)
        if not session:
            return None
        return Mapper.entity_to_dto(session, GameSessionResponseDTO)

    async def find_game_id_by_event_title(self, event_title: str) -> Optional[UUID]:
        """Ищет game_id по названию Discord-события. Для слушателей событий."""
        return await self.repo.find_game_id_by_event_title(event_title)

    async def get_game_by_session(self, session_id: UUID) -> Optional[Game]:
        """Возвращает игру по session_id."""
        session = await self._get_or_raise(session_id)
        return await self.game_repo.get_by_id(session.game_id)

    async def get_game_by_game_id(self, game_id: UUID) -> Optional[Game]:
        """Возвращает игру по game_id. Для /session info."""
        return await self.game_repo.get_by_id(game_id)

    async def get_discord_state(self, session_id: UUID) -> Optional[dict]:
        """Публичный доступ к discord_state сессии."""
        return await self.repo.get_discord_state(session_id)

    async def get_accepted_players_with_discord(self, session_id: UUID) -> list[tuple[int, str]]:
        """Принятые игроки с discord_id для сессии."""
        session = await self._get_or_raise(session_id)
        return await self.repo.get_accepted_players_with_discord(session.game_id)

    async def get_player_characters(self, session_id: UUID, discord_ids: list[int]) -> dict[int, str]:
        """Маппинг {discord_id: character_name} для участников сессии."""
        session = await self._get_or_raise(session_id)
        return await self.repo.get_player_characters(session.game_id, discord_ids)