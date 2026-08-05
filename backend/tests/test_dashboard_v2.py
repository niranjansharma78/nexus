from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_contains_current_core_sections():
    html = (ROOT / "app/templates/index.html").read_text(encoding="utf-8")

    for marker in [
        "NEXUS HOME",
        "NEEDS YOU",
        "YOUR WORLDS",
        "SIGNALS",
        "HANDLED FOR YOU",
        "BANKING ACTIVITY",
        "QUICK NOTE",
        "RELEVANT NOW",
    ]:
        assert marker in html
