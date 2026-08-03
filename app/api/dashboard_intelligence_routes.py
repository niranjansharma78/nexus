from fastapi import APIRouter
from app.services.dashboard_intelligence_service import dashboard_intelligence

router = APIRouter()

@router.get('/api/dashboard-intelligence')
def get_dashboard_intelligence():
    return dashboard_intelligence()
