#app/validators/auth_validators.py

import re
from app.exceptions.common_exceptions import ValidationError


class LoginValidator:
    """
    Business validation for login field.
    """

    LOGIN_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")

    @staticmethod
    def validate(login: str) -> None:
        if not LoginValidator.LOGIN_PATTERN.match(login):
            raise ValidationError(
                "Login must contain only letters, numbers and underscore (3-30 chars)"
            )


class PasswordValidator:

    # Минимум:
    # - 8+ символов
    # - 1 uppercase
    # - 1 lowercase
    # - 1 digit
    # - 1 special character
    STRONG_PASSWORD_PATTERN = re.compile(
        r"""
        ^
        (?=.*[a-z])        # хотя бы одна строчная
        (?=.*[A-Z])        # хотя бы одна заглавная
        (?=.*\d)           # хотя бы одна цифра
        (?=.*[@$!%*?&])    # хотя бы один спецсимвол
        .{8,}              # любые символы, минимум 8
        $
        """,
        re.VERBOSE
    )

    @staticmethod
    def validate_strength(password: str) -> None:

        if not PasswordValidator.STRONG_PASSWORD_PATTERN.match(password):
            raise ValidationError(
                "Password must be at least 8 characters long and include "
                "uppercase, lowercase, number and special character."
            )