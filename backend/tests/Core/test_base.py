from uuid import uuid4

from app.core.base import SoftDeleteMixin


class DummySoftDelete(SoftDeleteMixin):
    pass


def test_soft_delete_and_restore():
    entity = DummySoftDelete()
    actor_id = uuid4()
    entity.is_deleted = False
    entity.deleted_at = None
    entity.deleted_by = None

    entity.soft_delete(actor_id)
    assert entity.is_deleted is True
    assert entity.deleted_at is not None
    assert entity.deleted_by == actor_id

    entity.restore()
    assert entity.is_deleted is False
    assert entity.deleted_at is None
    assert entity.deleted_by is None
