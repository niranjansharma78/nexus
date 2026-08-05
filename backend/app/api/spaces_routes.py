from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.spaces_service import (
    assign_mailbox_to_space,
    create_space,
    delete_or_archive_space,
    list_mailboxes_with_spaces,
    list_spaces,
    set_default_space,
    update_space,
)


BASE = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE / "templates")
router = APIRouter()


class SpaceCreate(BaseModel):
    name: str
    world: str
    description: str | None = None
    color_key: str | None = None
    icon_key: str | None = None
    allow_cross_world: bool = False


class SpaceUpdate(SpaceCreate):
    pass


class SpaceDelete(BaseModel):
    move_to_space_id: int | None = None


class MailboxAssign(BaseModel):
    mailbox_profile_id: int
    space_id: int


@router.get("/connections", response_class=HTMLResponse)
def page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="connections_spaces.html",
        context={},
    )


@router.get("/api/spaces")
def spaces(include_archived: bool = False):
    return list_spaces(include_archived=include_archived)


@router.post("/api/spaces")
def add_space(payload: SpaceCreate):
    try:
        return create_space(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.put("/api/spaces/{space_id}")
def edit_space(space_id: int, payload: SpaceUpdate):
    try:
        return update_space(space_id, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/spaces/{space_id}/default")
def make_default(space_id: int):
    try:
        return set_default_space(space_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/api/spaces/{space_id}")
def remove_space(space_id: int, payload: SpaceDelete | None = None):
    try:
        return delete_or_archive_space(
            space_id,
            move_to_space_id=(
                payload.move_to_space_id
                if payload is not None
                else None
            ),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/api/connections/mailboxes")
def mailboxes():
    return list_mailboxes_with_spaces()


@router.post("/api/connections/mailboxes/assign")
def assign(payload: MailboxAssign):
    try:
        return assign_mailbox_to_space(
            payload.mailbox_profile_id,
            payload.space_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
