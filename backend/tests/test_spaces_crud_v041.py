from uuid import uuid4

from app.services.spaces_service import (
    create_space,
    delete_or_archive_space,
    list_spaces,
    update_space,
)


def test_create_update_delete_empty_space():
    name = f"Test World {uuid4().hex[:8]}"

    created = create_space(
        name=name,
        world="custom",
        description="Temporary test",
        allow_cross_world=True,
    )
    assert created["name"] == name

    updated = update_space(
        created["id"],
        name=f"{name} Updated",
        world="digital",
        description="Updated",
        allow_cross_world=False,
    )
    assert updated["world"] == "digital"

    result = delete_or_archive_space(created["id"])
    assert result["action"] == "deleted"

    active_ids = {space["id"] for space in list_spaces()}
    assert created["id"] not in active_ids
