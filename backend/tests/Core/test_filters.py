import pytest
from pydantic import ValidationError

from app.core.filters import CommonFilterParams
from app.core.enums import SortOrder


def test_filter_normalizes_text():
    filters = CommonFilterParams(
        q="  cliente  ",
        order=SortOrder.ASC,
    )

    assert filters.q == "cliente"


def test_filter_rejects_invalid_period():
    with pytest.raises(ValidationError):
        CommonFilterParams(
            created_after="2026-07-20T00:00:00Z",
            created_before="2026-07-10T00:00:00Z",
        )
