#app/domain/enums/game_session_status_enum.py

from enum import Enum

class GameSessionStatusEnum(str, Enum):
    """
    Status of a game session.

    Attributes:
        CREATED: Session entity has been created.
        ACTIVE: Session is currently running.
        COMPLETED: Session has finished normally.
        CANCELED: Session was canceled (scheduled event removed).
        INVALID: Session was invalidated by administrator.
    """
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"
    INVALID = "invalid"