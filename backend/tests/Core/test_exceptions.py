from app.core.exceptions import (
    ApplicationException,
    DuplicateResourceException,
    ResourceNotFoundException,
)


def test_application_exception_to_dict():
    error = ApplicationException(message="Falha.", code="CONTROLLED")
    assert error.to_dict() == {"code": "CONTROLLED", "message": "Falha."}


def test_resource_not_found_context():
    error = ResourceNotFoundException(resource="Cliente", resource_id="abc")
    assert error.message == "Cliente não encontrado."
    assert error.details["resource_id"] == "abc"


def test_duplicate_resource_defaults():
    error = DuplicateResourceException()
    assert error.code == "DUPLICATE_RESOURCE"
