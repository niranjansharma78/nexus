from pathlib import Path
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.developer_console_service import summary, evidence

BASE=Path(__file__).resolve().parents[1]
templates=Jinja2Templates(directory=BASE/"templates")
router=APIRouter()

@router.get("/developer-console",response_class=HTMLResponse)
def console(request:Request):
    return templates.TemplateResponse(request=request,name="developer_console.html",context={"summary":summary()})

@router.get("/evidence-explorer",response_class=HTMLResponse)
def explorer(request:Request):
    return templates.TemplateResponse(request=request,name="evidence_explorer.html",context={})

@router.get("/api/developer/evidence")
def evidence_api(limit:int=Query(200,ge=1,le=500),source:str|None=None,domain:str|None=None,category:str|None=None,min_signal:int|None=Query(None,ge=0,le=100),q:str|None=None):
    return evidence(limit,source or None,domain or None,category or None,min_signal,q or None)
