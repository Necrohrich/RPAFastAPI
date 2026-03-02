# app/domain/policies/base_policy.py
from app.exceptions.common_exceptions import PermissionDenied


class BasePolicy:
    @staticmethod
    def deny(message: str = "Forbidden"):
        raise PermissionDenied(message)