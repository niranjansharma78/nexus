from __future__ import annotations
import argparse, importlib, json, os, platform, sqlite3, subprocess, sys
from pathlib import Path

REQUIRED = ("fastapi", "uvicorn", "jinja2", "multipart", "itsdangerous", "httpx")

def module_version(name: str) -> str:
    try:
        module = importlib.import_module(name)
        return str(getattr(module, "__version__", "installed"))
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"

def collect():
    root = Path(__file__).resolve().parents[1]
    app_main = root / "app" / "main.py"
    report = {
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "is_3_14": sys.version_info[:2] == (3, 14),
        },
        "platform": platform.platform(),
        "project": {"root": str(root), "app_main_exists": app_main.exists(), "cwd": os.getcwd()},
        "modules": {name: module_version(name) for name in REQUIRED},
        "sqlite": sqlite3.sqlite_version,
    }
    result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
    report["pip"] = result.stdout.strip() or result.stderr.strip()
    errors = [f"{k}: {v}" for k, v in report["modules"].items() if str(v).startswith("ERROR:")]
    report["status"] = {"ok": report["python"]["is_3_14"] and app_main.exists() and not errors, "errors": errors}
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = collect()
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    return 0 if report["status"]["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
