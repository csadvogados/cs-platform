from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.constants import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)


@dataclass(slots=True)
class PasswordPolicyResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class PasswordPolicy:
    """
    Política oficial de senha.

    Regras padrão:
    - comprimento entre 12 e 128 caracteres;
    - ao menos uma letra minúscula;
    - ao menos uma letra maiúscula;
    - ao menos um número;
    - ao menos um caractere especial;
    - não pode conter o e-mail completo;
    """

    LOWERCASE_PATTERN = re.compile(r"[a-z]")
    UPPERCASE_PATTERN = re.compile(r"[A-Z]")
    DIGIT_PATTERN = re.compile(r"\d")
    SPECIAL_PATTERN = re.compile(r"[^A-Za-z0-9]")

    @classmethod
    def validate(
        cls,
        password: str,
        *,
        email: str | None = None,
    ) -> PasswordPolicyResult:
        errors: list[str] = []

        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(
                f"A senha deve possuir pelo menos "
                f"{PASSWORD_MIN_LENGTH} caracteres."
            )

        if len(password) > PASSWORD_MAX_LENGTH:
            errors.append(
                f"A senha deve possuir no máximo "
                f"{PASSWORD_MAX_LENGTH} caracteres."
            )

        if not cls.LOWERCASE_PATTERN.search(password):
            errors.append(
                "A senha deve possuir ao menos uma letra minúscula."
            )

        if not cls.UPPERCASE_PATTERN.search(password):
            errors.append(
                "A senha deve possuir ao menos uma letra maiúscula."
            )

        if not cls.DIGIT_PATTERN.search(password):
            errors.append(
                "A senha deve possuir ao menos um número."
            )

        if not cls.SPECIAL_PATTERN.search(password):
            errors.append(
                "A senha deve possuir ao menos um caractere especial."
            )

        if email:
            normalized_email = email.strip().lower()
            if normalized_email and normalized_email in password.lower():
                errors.append(
                    "A senha não pode conter o e-mail completo."
                )

        return PasswordPolicyResult(
            is_valid=not errors,
            errors=errors,
        )

    @classmethod
    def ensure_valid(
        cls,
        password: str,
        *,
        email: str | None = None,
    ) -> None:
        result = cls.validate(password, email=email)

        if not result.is_valid:
            raise ValueError(" ".join(result.errors))


__all__ = [
    "PasswordPolicy",
    "PasswordPolicyResult",
]
