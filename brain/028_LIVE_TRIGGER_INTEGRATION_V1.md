# ADR-028: Live Trigger Integration v1

Status: Accepted
Brain version: 2.1.0 Alpha 1

Live Trigger Integration connects external observations to Cognitive Runtime v2.

## Supported trigger kinds

- evidence
- event
- schedule
- manual

## Core rules

- Duplicate triggers are suppressed by deterministic fingerprint.
- Triggers can be processed immediately or queued.
- Trigger persistence is separate from cognitive engines.
- Runtime remains non-executing.
- A failed trigger does not corrupt unrelated engine state.
