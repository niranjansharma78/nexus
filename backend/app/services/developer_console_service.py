from app.core.database import get_connection

def ensure_columns():
    with get_connection() as c:
        existing={r[1] for r in c.execute("PRAGMA table_info(evidence)").fetchall()}
        for n,ddl in {"category":"TEXT","signal_score":"INTEGER NOT NULL DEFAULT 0","relationship_impact":"TEXT NOT NULL DEFAULT 'neutral'"}.items():
            if n not in existing:
                c.execute(f"ALTER TABLE evidence ADD COLUMN {n} {ddl}")

def summary():
    ensure_columns()
    with get_connection() as c:
        totals={
            "evidence":c.execute("SELECT COUNT(*) FROM evidence").fetchone()[0],
            "imap":c.execute("SELECT COUNT(*) FROM evidence WHERE source='IMAP'").fetchone()[0],
            "decisions":c.execute("SELECT COUNT(*) FROM evidence WHERE requires_decision=1").fetchone()[0],
            "high_signal":c.execute("SELECT COUNT(*) FROM evidence WHERE COALESCE(signal_score,0)>=70").fetchone()[0],
            "avg_confidence":round(c.execute("SELECT COALESCE(AVG(confidence),0) FROM evidence").fetchone()[0]*100),
        }
        by_domain=[dict(r) for r in c.execute("SELECT domain,COUNT(*) count FROM evidence GROUP BY domain ORDER BY count DESC")]
        by_category=[dict(r) for r in c.execute("SELECT COALESCE(category,'uncategorized') category,COUNT(*) count FROM evidence GROUP BY COALESCE(category,'uncategorized') ORDER BY count DESC")]
        try:
            mailboxes=[dict(r) for r in c.execute("SELECT label,username,last_scan_at,last_scan_count FROM mailbox_profiles ORDER BY id DESC")]
        except Exception:
            mailboxes=[]
    return {"totals":totals,"by_domain":by_domain,"by_category":by_category,"mailboxes":mailboxes}

def evidence(limit=200,source=None,domain=None,category=None,min_signal=None,q=None):
    ensure_columns()
    clauses=["1=1"]; params=[]
    if source: clauses.append("source=?"); params.append(source)
    if domain: clauses.append("domain=?"); params.append(domain)
    if category: clauses.append("COALESCE(category,'uncategorized')=?"); params.append(category)
    if min_signal is not None: clauses.append("COALESCE(signal_score,0)>=?"); params.append(min_signal)
    if q:
        clauses.append("(title LIKE ? OR summary LIKE ? OR entity_name LIKE ?)")
        token=f"%{q}%"; params += [token,token,token]
    params.append(max(1,min(limit,500)))
    sql=f'''SELECT id,source,title,summary,domain,occurred_at,confidence,status,entity_name,
                   requires_decision,priority,COALESCE(category,'uncategorized') category,
                   COALESCE(signal_score,0) signal_score,
                   COALESCE(relationship_impact,'neutral') relationship_impact
            FROM evidence WHERE {' AND '.join(clauses)}
            ORDER BY id DESC LIMIT ?'''
    with get_connection() as c:
        return [dict(r) for r in c.execute(sql,params)]
