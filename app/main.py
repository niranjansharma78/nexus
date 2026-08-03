from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router
from app.api.developer_console_routes import router as developer_console_router
from app.api.imap_routes import router as imap_router
from app.core.database import init_db

BASE = Path(__file__).resolve().parent
app = FastAPI(title="Nexus DP1", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")
templates = Jinja2Templates(directory=BASE/"templates")
app.include_router(router)
app.include_router(developer_console_router)
app.include_router(imap_router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/developer", response_class=HTMLResponse)
def developer(request: Request):
    return templates.TemplateResponse("developer.html", {"request": request})
