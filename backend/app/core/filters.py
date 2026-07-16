from __future__ import annotations

from datetime import datetime

from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from app.core.enums import SortOrder


class CommonFilterParams(BaseModel):
    q: str | None = Field(
        default=None,
        max_length=200,
        description="Pesquisa textual.",
    )
    status: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    sort: str | None = None
    order: SortOrder = SortOrder.ASC

    @field_validator("q", "status", "sort")
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("created_before")
    @classmethod
    def validate_period(
        cls,
        value: datetime | None,
        info,
    ) -> datetime | None:
        created_after = info.data.get("created_after")

        if (
            value is not None
            and created_after is not None
            and value < created_after
        ):
            raise ValueError(
                "created_before deve ser posterior a created_after."
            )

        return value


def common_filters(
    q: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    sort: str | None = Query(default=None),
    order: SortOrder = Query(default=SortOrder.ASC),
) -> CommonFilterParams:
    return CommonFilterParams(
        q=q,
        status=status,
        created_after=created_after,
        created_before=created_before,
        sort=sort,
        order=order,
    )


__all__ = ["CommonFilterParams", "common_filters"]
