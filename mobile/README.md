# Nexus Mobile v1.3 — Dynamic Worlds and Confidence

## Dynamic Worlds

The Worlds screen now supports:

- Add World
- Edit name, type and description
- Enable or disable cross-World intelligence
- Set a default World
- Delete an empty World
- Safely archive a World that contains mailboxes
- Pull to refresh

Deleting or archiving a World never deletes its underlying email evidence.

## Confidence meters restored

Confidence appears on:

- Alerts and Important Updates
- Open Loops
- Evidence summaries

Labels:

- 85–100%: High
- 60–84%: Likely
- Below 60%: Review

## Required backend

Use Nexus Backend Release 0.4.1. It adds the World create, edit, default, delete and archive APIs.

## Installation

Backend:

```bat
D:\Nexus_Backend_0_4_1
```

Copy the previous `data\nexus.db`, recreate the virtual environment, install requirements and run tests.

Mobile:

```bat
D:\Nexus_Mobile_v1_3
clean_setup_android.bat
run_phone.bat
```
