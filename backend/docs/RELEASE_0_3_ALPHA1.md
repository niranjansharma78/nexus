# Nexus Backend 0.3 Alpha 1

This release connects Attachment Intelligence to real IMAP scans.

## New behaviour

When a new email is scanned, Nexus now:

1. stores the email evidence
2. extracts business events from the email body
3. captures attached files
4. saves attachments under `data/attachments`
5. analyzes supported PDF, Excel, CSV, DOCX and TXT files
6. creates structured business events from attachments
7. exposes those events through an executive feed API

## New scan response

Mailbox scans now include:

- `attachments_saved`
- `business_events_created`

## Executive feed

Open:

`http://127.0.0.1:8010/api/v1/executive/feed`

The response contains:

- alerts
- notices
- delegations
- monitoring

This API is the direct data source for the future Flutter Home screen.

## Installation

Use this as a complete replacement release in a new folder:

```bat
D:\Nexus_0_3_Alpha1
```

Copy your existing database from:

```text
D:\Nexus_0_2\data\nexus.db
```

to:

```text
D:\Nexus_0_3_Alpha1\data\nexus.db
```

Then:

```bat
cd /d D:\Nexus_0_3_Alpha1
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\migrate.py
.venv\Scripts\python scripts\migrate_attachment_v1.py
.venv\Scripts\python -m pytest
run.bat
```

Scan a mailbox again. Only newly inserted messages are processed because duplicates remain protected.
