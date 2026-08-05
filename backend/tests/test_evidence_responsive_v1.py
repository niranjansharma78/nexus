from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_responsive_assets_exist():
    assert (
        ROOT / "app/static/css/evidence_responsive_v1.css"
    ).exists()
    assert (
        ROOT / "app/static/js/evidence_responsive_v1.js"
    ).exists()


def test_css_prevents_horizontal_scroll():
    css = (
        ROOT / "app/static/css/evidence_responsive_v1.css"
    ).read_text(encoding="utf-8")

    assert "overflow-x: hidden" in css
    assert "table-layout: fixed" in css
    assert "grid-template-columns: 92px minmax(0, 1fr)" in css


def test_js_adds_mobile_labels():
    js = (
        ROOT / "app/static/js/evidence_responsive_v1.js"
    ).read_text(encoding="utf-8")

    assert "dataset.label" in js
    assert "MutationObserver" in js
