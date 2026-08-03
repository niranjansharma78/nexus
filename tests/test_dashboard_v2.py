from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_dashboard_v2_files_exist():
    assert (ROOT / "app/templates/index.html").exists()
    assert (ROOT / "app/static/css/dashboard_v2.css").exists()
    assert (ROOT / "app/static/js/dashboard_v2.js").exists()

def test_dashboard_contains_core_sections():
    html = (ROOT / "app/templates/index.html").read_text(encoding="utf-8")
    for marker in [
        "NEXUS AT WORK",
        "NEEDS YOUR JUDGEMENT",
        "YOUR WORKSPACE",
        "SIGNALS",
        "QUICK NOTE",
        "DYNAMIC ZONE",
    ]:
        assert marker in html
