from datetime import datetime

MONITOR_CATEGORIES={"operations","procurement","finance","compliance"}
OWNER_HINTS={
 "production":"Planning","dispatch":"Planning","despatch":"Planning",
 "shipment":"Logistics","stock":"Stores","reconciliation":"Finance",
 "invoice":"Accounts","payment":"Finance","candidate":"HR",
 "interview":"HR","purchase order":"Procurement","quotation":"Sales","rfq":"Sales"
}

def _text(x):
    return f"{x.get('title','')} {x.get('summary','')}".lower()

def infer_owner(x):
    text=_text(x)
    for term,owner in OWNER_HINTS.items():
        if term in text:
            return owner
    return None

def summarize_item(x):
    title=str(x.get("title") or "Update").strip()
    summary=str(x.get("summary") or "").strip()
    if summary and not summary.lower().startswith("email from"):
        return summary[:240]
    low=title.lower()
    if "production confirmation" in low:
        return "Production has been confirmed. Planning can prepare the next operational step."
    if "dispatch details" in low or "despatch details" in low:
        return "Dispatch information has been received and can be monitored for completion."
    if "stock level" in low:
        return "Updated stock position has been received for operational review."
    if "reconciliation" in low:
        return "Reconciliation information has been received for finance review."
    if "candidate" in low or "workindia" in low:
        return "A recruitment update was received and grouped with other hiring activity."
    return summary or "A relevant update was received."

def classify_executive_role(x):
    attention=str(x.get("attention_type") or "information")
    category=str(x.get("category") or "")
    text=_text(x)
    if attention=="decision": return "needs_you"
    if attention=="follow_up": return "delegate"
    if attention=="signal": return "monitor"
    if attention=="grouped": return "handled"
    if category in MONITOR_CATEGORIES: return "monitor"
    if any(t in text for t in {"production","dispatch","despatch","stock","reconciliation"}): return "monitor"
    return "handled"

def build_executive_brief(recent_items, grouped_recruitment=None, declining_relationships=None):
    sections={"needs_you":[],"delegate":[],"monitor":[],"handled":[]}
    for x in recent_items:
        role=classify_executive_role(x)
        sections[role].append({
            "id":x.get("id"),"title":x.get("title") or "Update",
            "summary":summarize_item(x),"domain":x.get("domain") or "digital",
            "category":x.get("category") or "communication",
            "confidence":float(x.get("confidence") or 0),
            "priority":int(x.get("brain_priority") or x.get("signal_score") or 0),
            "owner":infer_owner(x),"source":x.get("source"),
            "occurred_at":x.get("occurred_at")
        })
    for g in grouped_recruitment or []:
        sections["handled"].append({
            "id":None,"title":g.get("title") or "Recruitment activity",
            "summary":g.get("summary") or "Recruitment items were grouped.",
            "domain":"business","category":"recruitment","confidence":0.9,
            "priority":20,"owner":"HR","source":"Grouped evidence","occurred_at":g.get("date")
        })
    for key,limit in [("needs_you",5),("delegate",5),("monitor",6),("handled",6)]:
        sections[key]=sorted(sections[key],key=lambda x:x["priority"],reverse=True)[:limit]
    reviewed=len(recent_items)
    meaningful=sum(len(sections[k]) for k in ("needs_you","delegate","monitor"))
    if sections["needs_you"]:
        headline=f"{len(sections['needs_you'])} item(s) need your judgement."
    elif sections["delegate"]:
        headline=f"{len(sections['delegate'])} item(s) should be delegated."
    elif sections["monitor"]:
        headline=f"{len(sections['monitor'])} important update(s) are worth knowing."
    else:
        headline="Everything important is under control."
    return {
      "generated_at":datetime.now().isoformat(),
      "headline":headline,
      "summary":{
        "reviewed":reviewed,"hidden":max(0,reviewed-meaningful),
        "needs_you":len(sections["needs_you"]),"delegate":len(sections["delegate"]),
        "monitor":len(sections["monitor"]),"handled":len(sections["handled"]),
        "estimated_minutes_saved":max(5,reviewed*2)
      },
      **sections,
      "relationship_watch":(declining_relationships or [])[:5]
    }
