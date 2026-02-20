# app/infrastructure/security/jwt_provider.py
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import jwt
from app.core.config import settings

class JWTProvider:
    """
    Провайдер для создания и проверки JWT-токенов.

    Особенности:
        - Использует UUID в качестве user_id.
        - timezone-aware datetime для exp и iat.
        - Добавляет уникальный идентификатор токена (jti).
        - Метод статический, не требует создания экземпляра.
    """

    @staticmethod
    def create_access_token(user_id: UUID, token_version: int) -> str:
        """
        Создаёт JWT access-токен для пользователя.

        Args:
            user_id (UUID): ID пользователя.
            token_version (int): Версия токена для ротации.

        Returns:
            str: Подписанный JWT-токен.
        """
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),  # UUID -> str
            "ver": token_version,
            "iat": now,
            "exp": exp,
            "jti": str(uuid4()),  # уникальный идентификатор токена
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Декодирует JWT-токен и возвращает payload.

        Raises:
            jwt.ExpiredSignatureError: Если токен просрочен.
            jwt.InvalidTokenError: Если токен недействителен.
        """
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload