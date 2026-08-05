from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.connectors.imap_sensor import IMAPSensorError
from app.services.imap_service import list_profiles, scan_mailbox

BASE = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE / "templates")

router = APIRouter()


@router.get("/mailboxes", response_class=HTMLResponse)
def mailboxes_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="mailboxes.html",
        context={
            "profiles": list_profiles(),
            "result": None,
            "error": None,
        },
    )


@router.post("/mailboxes/scan", response_class=HTMLResponse)
def mailboxes_scan(
    request: Request,
    label: str = Form(...),
    host: str = Form(...),
    port: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    folder: str = Form("INBOX"),
    use_ssl: str | None = Form(None),
    limit: int = Form(50),
):
    try:
        result = scan_mailbox(
            label=label,
            host=host,
            port=port,
            username=username,
            password=password,
            folder=folder,
            use_ssl=bool(use_ssl),
            limit=max(1, min(limit, 500)),
        )

        return templates.TemplateResponse(
            request=request,
            name="mailboxes.html",
            context={
                "profiles": list_profiles(),
                "result": result,
                "error": None,
            },
        )

    except IMAPSensorError as exc:
        return templates.TemplateResponse(
            request=request,
            name="mailboxes.html",
            context={
                "profiles": list_profiles(),
                "result": None,
                "error": str(exc),
            },
            status_code=400,
        )