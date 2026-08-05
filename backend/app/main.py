from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router
from app.api.banking_highlights_routes import router as banking_highlights_router
from app.api.spaces_routes import router as spaces_router
from app.api.delegation_board_routes import router as delegation_board_router
from app.api.delegation_routes import router as delegation_router
from app.api.executive_brief_routes import router as executive_brief_router
from app.api.brain_routes import router as brain_router
from app.api.dashboard_intelligence_routes import router as dashboard_intelligence_router
from app.api.developer_console_routes import router as developer_console_router
from app.api.imap_routes import router as imap_router
from app.core.database import init_db
from app.core.migrations import run_migrations
from app.api.v1.intelligence_routes import router as intelligence_v1_router
from app.api.v1.system_routes import router as system_v1_router
from app.api.v1.attachment_routes import router as attachment_v1_router
from app.api.v1.executive_feed_routes import router as executive_feed_v1_router
from app.api.v1.conversation_routes import router as conversation_v1_router
from app.api.v1.feedback_routes import router as feedback_v1_router

BASE = Path(__file__).resolve().parent
app = FastAPI(title="Nexus Intelligence OS", version="0.4.1")
app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")
templates = Jinja2Templates(directory=BASE/"templates")
app.include_router(router)
app.include_router(banking_highlights_router)
app.include_router(spaces_router)
app.include_router(delegation_board_router)
app.include_router(delegation_router)
app.include_router(executive_brief_router)
app.include_router(brain_router)
app.include_router(dashboard_intelligence_router)
app.include_router(developer_console_router)
app.include_router(imap_router)
app.include_router(intelligence_v1_router)
app.include_router(system_v1_router)
app.include_router(attachment_v1_router)
app.include_router(executive_feed_v1_router)
app.include_router(conversation_v1_router)
app.include_router(feedback_v1_router)

@app.on_event("startup")
def startup():
    init_db()
    run_migrations()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )

@app.get("/developer", response_class=HTMLResponse)
def developer(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="developer.html",
        context={},
    )