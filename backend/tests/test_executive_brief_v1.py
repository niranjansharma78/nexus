from app.brain.executive_brief_engine import build_executive_brief,classify_executive_role,infer_owner

def test_production_confirmation_is_monitored():
    x={"title":"Production Confirmation | Claron","summary":"Production confirmed.","category":"operations","attention_type":"information"}
    assert classify_executive_role(x)=="monitor"
    assert infer_owner(x)=="Planning"

def test_followup_is_delegated():
    x={"title":"Payment pending","summary":"Please update the status.","category":"finance","attention_type":"follow_up"}
    assert classify_executive_role(x)=="delegate"

def test_brief_monitor_section():
    b=build_executive_brief([{"id":1,"title":"Production Confirmation","summary":"Production confirmed.","domain":"business","category":"operations","attention_type":"information","confidence":0.9,"brain_priority":45,"source":"IMAP","occurred_at":"2026-08-04"}])
    assert b["summary"]["monitor"]==1
    assert b["monitor"][0]["owner"]=="Planning"
