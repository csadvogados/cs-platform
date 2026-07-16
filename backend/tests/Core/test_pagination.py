from app.core.pagination import Page, PaginationParams


def test_pagination_offset():
    params = PaginationParams(page=3, page_size=25)

    assert params.offset == 50
    assert params.limit == 25


def test_page_calculates_pages():
    page = Page[int].create(
        items=[1, 2],
        page=1,
        page_size=2,
        total=5,
    )

    assert page.pages == 3
