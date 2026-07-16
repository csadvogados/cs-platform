from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
)


T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(
            DEFAULT_PAGE,
            ge=1,
            description="Número da página.",
        ),
        page_size: int = Query(
            DEFAULT_PAGE_SIZE,
            ge=MIN_PAGE_SIZE,
            le=MAX_PAGE_SIZE,
            description="Quantidade de itens por página.",
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)

    @classmethod
    def create(
        cls,
        *,
        items: list[T],
        page: int,
        page_size: int,
        total: int,
    ) -> "Page[T]":
        pages = ceil(total / page_size) if total > 0 else 0
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
        )


__all__ = ["PaginationParams", "Page"]
