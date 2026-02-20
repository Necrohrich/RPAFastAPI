# tests/test_jwt_provider.py
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from app.infrastructure.security.jwt_provider import JWTProvider
from app.core.config import settings

def test_create_and_decode_access_token():
    user_id = uuid4()
    token_version = 1

    # Создаём токен
    token = JWTProvider.create_access_token(user_id=user_id, token_version=token_version)
    assert isinstance(token, str) and len(token) > 0

    # Декодируем токен с помощью decode_token
    payload = JWTProvider.decode_token(token)
    assert isinstance(payload, dict)

    # Проверяем обязательные поля
    assert payload["sub"] == str(user_id)
    assert payload["ver"] == token_version
    assert "iat" in payload
    assert "exp" in payload
    assert "jti" in payload

    # Проверяем что exp > iat и примерно соответствует настройке
    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected_exp = iat + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Допускаем разницу в несколько секунд
    delta = exp - expected_exp
    assert abs(delta.total_seconds()) < 5

    # Проверяем что sub можно обратно преобразовать в UUID
    assert isinstance(UUID(payload["sub"]), UUID)