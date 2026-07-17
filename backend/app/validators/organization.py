from __future__ import annotations
import re

_ONLY_DIGITS = re.compile(r"\D+")
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")

def only_digits(value: str) -> str:
    return _ONLY_DIGITS.sub("", value)

def normalize_brazilian_tax_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = only_digits(value.strip())
    return normalized or None

def validate_brazilian_tax_id(value: str) -> bool:
    cnpj = only_digits(value)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def digit(base: str, weights: list[int]) -> str:
        total = sum(int(n) * w for n, w in zip(base, weights, strict=True))
        remainder = total % 11
        return str(0 if remainder < 2 else 11 - remainder)

    d1 = digit(cnpj[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    d2 = digit(cnpj[:12] + d1, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    return cnpj[-2:] == d1 + d2

def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = only_digits(value)
    if not normalized:
        return None
    if len(normalized) not in {10, 11, 12, 13}:
        raise ValueError("Telefone inválido.")
    return normalized

def normalize_postal_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = only_digits(value)
    if not normalized:
        return None
    if len(normalized) != 8:
        raise ValueError("CEP inválido.")
    return normalized

def normalize_state_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    if len(normalized) != 2 or not normalized.isalpha():
        raise ValueError("UF inválida.")
    return normalized

def normalize_hex_color(value: str) -> str:
    normalized = value.strip().upper()
    if not _HEX_COLOR.fullmatch(normalized):
        raise ValueError("A cor deve utilizar o formato hexadecimal #RRGGBB.")
    return normalized
