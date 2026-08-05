from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_delegation_board_files_exist():
    assert (ROOT / "app/templates/delegation_board.html").exists()
    assert (ROOT / "app/static/css/delegation_board.css").exists()
    assert (ROOT / "app/static/js/delegation_board.js").exists()


def test_board_uses_delegation_api():
    js = (ROOT / "app/static/js/delegation_board.js").read_text(encoding="utf-8")
    assert "/api/delegations" in js
    assert 'method: "PATCH"' in js
