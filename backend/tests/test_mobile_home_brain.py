from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_mobile_home_files_exist():
    assert (ROOT / "app/templates/index.html").exists()
    assert (ROOT / "app/static/css/mobile_home.css").exists()
    assert (ROOT / "app/static/js/mobile_home.js").exists()

def test_mobile_home_uses_brain_api():
    js = (ROOT / "app/static/js/mobile_home.js").read_text(encoding="utf-8")
    assert "/api/brain/state" in js

def test_mobile_home_core_sections():
    html = (ROOT / "app/templates/index.html").read_text(encoding="utf-8")
    for marker in ["NEEDS YOU", "YOUR WORLDS", "SIGNALS", "HANDLED FOR YOU", "QUICK NOTE", "RELEVANT NOW"]:
        assert marker in html
