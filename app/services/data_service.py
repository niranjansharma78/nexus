from datetime import datetime
from app.core.database import get_connection

def dashboard_data():
    with get_connection() as conn:
        evidence = [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY occurred_at DESC LIMIT 24").fetchall()]
        decisions = [dict(r) for r in conn.execute("SELECT * FROM evidence WHERE requires_decision=1 ORDER BY priority, occurred_at DESC LIMIT 5").fetchall()]
        tiles = [dict(r) for r in conn.execute("SELECT * FROM workspace_tiles WHERE hidden=0 ORDER BY position").fetchall()]
        sources = [dict(r) for r in conn.execute("SELECT source,COUNT(*) count FROM evidence GROUP BY source ORDER BY count DESC").fetchall()]
        entities = [dict(r) for r in conn.execute("SELECT * FROM entities ORDER BY CASE trajectory WHEN 'declining' THEN 1 WHEN 'improving' THEN 2 ELSE 3 END, relationship_score ASC LIMIT 6").fetchall()]
        notes = [dict(r) for r in conn.execute("SELECT * FROM notes WHERE archived=0 ORDER BY pinned DESC,id DESC LIMIT 4").fetchall()]
        avg = conn.execute("SELECT COALESCE(AVG(confidence),0) FROM evidence").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    signals=[]
    for x in evidence:
        if x['requires_decision']: continue
        signals.append({**x,'signal_kind':'change'})
        if len(signals)>=6: break
    return {'summary':{'reviewed':total,'decision_count':len(decisions),'confidence':round(avg*100),'sources':sources,'saved_minutes':max(total*2,15)},'decisions':decisions,'signals':signals,'workspace':tiles,'entities':entities,'notes':notes}

def all_evidence(limit=100):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY occurred_at DESC LIMIT ?",(limit,)).fetchall()]

def all_entities(limit=100):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM entities ORDER BY name LIMIT ?",(limit,)).fetchall()]

def save_tile_order(tile_ids):
    with get_connection() as conn:
        for pos,tile_id in enumerate(tile_ids): conn.execute("UPDATE workspace_tiles SET position=? WHERE id=?",(pos,tile_id))

def add_note(text,domain='personal'):
    text=text.strip()
    if not text: raise ValueError('Note text is required')
    with get_connection() as conn:
        cur=conn.execute("INSERT INTO notes(text,domain,created_at) VALUES(?,?,?)",(text,domain,datetime.now().isoformat(timespec='seconds')))
        return {'id':cur.lastrowid,'text':text,'domain':domain}
