from app.core.schemas import ErrorDetail, PaginatedResponse, PaginationMeta, SuccessResponse


def test_success_response_generic() -> None:
    response = SuccessResponse[str](message="OK", data="payload")
    dumped = response.model_dump()
    assert dumped["success"] is True
    assert dumped["data"] == "payload"


def test_paginated_response_shape() -> None:
    response = PaginatedResponse[str](
        items=["a"],
        pagination=PaginationMeta(
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1,
        ),
    )
    dumped = response.model_dump()
    assert dumped["pagination"]["page"] == 1
    assert dumped["pagination"]["page_size"] == 20
    assert dumped["pagination"]["total_items"] == 1
    assert dumped["pagination"]["total_pages"] == 1


def test_error_detail_optional_field() -> None:
    detail = ErrorDetail(message="Invalid")
    assert detail.field is None
