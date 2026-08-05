from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.attachment_event_service import events_from_attachment
from app.services.attachment_intelligence_service import analyze_attachment


router = APIRouter(
    prefix="/api/v1/attachments",
    tags=["attachments"],
)


class AnalyzeRequest(BaseModel):
    path: str


@router.post("/analyze")
def analyze(payload: AnalyzeRequest):
    try:
        extraction = analyze_attachment(payload.path)
        result = extraction.to_dict()
        result["events"] = events_from_attachment(extraction)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Attachment not found: {exc}",
        ) from exc
    except (ValueError, RuntimeError, ImportError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
