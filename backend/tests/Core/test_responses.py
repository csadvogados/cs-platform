from app.core.responses import error_response, success_response


def test_success_response():
    payload = success_response(
        {"id": "1"},
        meta={"source": "test"},
    )

    assert payload["success"] is True
    assert payload["data"] == {"id": "1"}
    assert payload["meta"]["source"] == "test"


def test_error_response():
    payload = error_response(
        "TEST_ERROR",
        "Falha de teste.",
    )

    assert payload["success"] is False
    assert payload["error"]["code"] == "TEST_ERROR"
