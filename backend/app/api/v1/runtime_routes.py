from pathlib import Path

from fastapi import APIRouter

from app.brain.runtime.service import BrainRuntime


router = APIRouter(prefix="/api/v1/brain", tags=["brain-runtime"])


@router.post("/runtime/run")
def run_runtime_cycle():
    runtime = BrainRuntime(Path("data") / "nexus.db")
    return runtime.run_cycle().to_dict()
