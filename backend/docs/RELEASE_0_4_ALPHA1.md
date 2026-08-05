# Nexus Backend 0.4 Alpha 1

This release adds the first Cognitive Core capabilities.

## Conversation correlation

Business events can now be grouped into communication loops.

Examples:

- purchase order received
- production confirmed
- dispatch recorded
- delivery confirmation expected
- payment received
- cheque bounce resolution expected
- complaint resolution expected

Run:

```bat
.venv\Scripts\python scripts\correlate_conversations.py
```

API:

- `POST /api/v1/conversations/correlate`
- `GET /api/v1/conversations`

## Intelligence correction controls

Users can now explicitly correct the intelligence.

API:

- `POST /api/v1/intelligence-feedback`
- `GET /api/v1/intelligence-feedback/summary`

Supported feedback includes:

- always_alert
- always_show
- delegate_to
- suppress
- wrong_category
- wrong_company
- wrong_amount
- wrong_source
- internal_transfer
- not_relevant
- lock_rule
- unlock_rule

## Installation

Extract as:

```text
D:\Nexus_0_4_Alpha1
```

Copy your database from the previous release into:

```text
D:\Nexus_0_4_Alpha1\data\nexus.db
```

Then run:

```bat
cd /d D:\Nexus_0_4_Alpha1
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\migrate.py
.venv\Scripts\python scripts\migrate_attachment_v1.py
.venv\Scripts\python scripts\correlate_conversations.py
.venv\Scripts\python -m pytest
run.bat
```
