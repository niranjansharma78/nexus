from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.delegation_service import (
    create_delegation,
    list_delegations,
    set_monitor_status,
    update_delegation_status,
)

router = APIRouter(prefix="/api/delegations")


class DelegationCreate(BaseModel):
    evidence_id: int | None = None
    title: str
    summary: str | None = None
    owner: str
    note: str | None = None


class DelegationUpdate(BaseModel):
    status: str
    note: str | None = None


class MonitorUpdate(BaseModel):
    evidence_id: int
    status: str = Field(default="acknowledged")
    note: str | None = None


@router.get("")
def get_delegations(status: str | None = None):
    return list_delegations(status=status)


@router.post("")
def add_delegation(payload: DelegationCreate):
    try:
        return create_delegation(
            evidence_id=payload.evidence_id,
            title=payload.title,
            summary=payload.summary,
            owner=payload.owner,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{delegation_id}")
def change_delegation(delegation_id: int, payload: DelegationUpdate):
    try:
        return update_delegation_status(
            delegation_id=delegation_id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/monitor")
def update_monitor(payload: MonitorUpdate):
    try:
        return set_monitor_status(
            evidence_id=payload.evidence_id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
