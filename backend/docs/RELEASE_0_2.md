# Nexus Backend Release 0.2

This is the first consolidated release after the patch-based prototype stage.

## Included

- clean source tree without `.venv`, `.git`, caches, or old backups
- database migration framework
- structured business-event schema
- conversation and closure-watch schema
- attachment inventory schema
- user-feedback schema
- bank-account registry schema
- `/api/v1/system/health`
- `/api/v1/system/capabilities`
- `/api/v1/intelligence/interpret`
- first multi-event extraction rules
- explicit Alert, Notice, Delegate, and Monitor visibility
- compatibility with historical banking tests

## Install

Copy the release to a new folder, for example:

```bat
D:\Nexus_0_2
```

Copy your current database into:

```text
D:\Nexus_0_2\data\nexus.db
```

Then:

```bat
cd /d D:\Nexus_0_2
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\migrate.py
.venv\Scripts\python -m pytest
run.bat
```

## Validation

Open:

- `http://127.0.0.1:8010/api/v1/system/health`
- `http://127.0.0.1:8010/api/v1/system/capabilities`

Test interpretation using API docs:

- `http://127.0.0.1:8010/docs`
