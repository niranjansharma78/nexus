from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE / "templates")
router = APIRouter()


@router.get("/delegations", response_class=HTMLResponse)
def delegation_board(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="delegation_board.html",
        context={},
    )
