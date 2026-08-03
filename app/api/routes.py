from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from app.services.data_service import dashboard_data,all_evidence,all_entities,save_tile_order,add_note
router=APIRouter(prefix='/api')
class TileOrder(BaseModel): tile_ids:list[str]
class NoteIn(BaseModel):
    text:str=Field(min_length=1,max_length=500)
    domain:str='personal'
@router.get('/health')
def health(): return {'status':'healthy','external_system_mode':'read-only','build':'DP1-B002'}
@router.get('/dashboard')
def dashboard(): return dashboard_data()
@router.get('/evidence')
def evidence(limit:int=100): return all_evidence(max(1,min(limit,500)))
@router.get('/entities')
def entities(limit:int=100): return all_entities(max(1,min(limit,500)))
@router.put('/workspace/order')
def workspace_order(payload:TileOrder): save_tile_order(payload.tile_ids); return {'saved':True}
@router.post('/notes')
def create_note(payload:NoteIn):
    try: return add_note(payload.text,payload.domain)
    except ValueError as e: raise HTTPException(400,str(e))
