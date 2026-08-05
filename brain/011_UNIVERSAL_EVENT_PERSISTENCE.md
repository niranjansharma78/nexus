# ADR-011: Universal Event Persistence

Status: Accepted  
Brain version: 0.5.0 Milestone 6

Milestone 6 introduces durable SQLite persistence for Universal Events.

## Responsibilities

The repository supports:

- schema creation
- save and upsert
- retrieval by event ID
- filtering by World
- filtering by closure
- filtering by universal transition
- filtering by evidence
- counting
- explicit deletion

## Design rules

- The repository stores only the universal model.
- It does not contain industry-specific columns.
- Objects, parties, value and metadata are serialized without changing their
  universal meaning.
- Persistence remains separate from event inference.
- Existing email, banking and attachment pipelines are not changed in this
  milestone.
- Live data is never added to Git.

## Database location

The migration script prepares the table in:

`backend/data/nexus.db`

The database remains local and ignored by Git.
