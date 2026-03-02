# app/infrastructure/security/refresh_token_provider.py

import hashlib
import secrets

class RefreshTokenProvider:

    @staticmethod
    def generate() -> str:
        return secrets.token_urlsafe(64)

    @staticmethod
    def hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()