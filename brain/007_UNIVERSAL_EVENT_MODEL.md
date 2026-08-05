# ADR-007: Universal Event Model

Status: Accepted  
Brain version: 0.5.0 Milestone 2

Milestone 2 introduces the canonical in-memory event model.

## Core objects

### UniversalObjectRef
Represents any person, organization, document, asset, commitment, transaction,
resource, task, relationship or other universal object.

### ValueMeasure
Carries money, quantity, unit and importance without assuming any industry.

### UniversalEvent
Represents a real-world state transition with:
- object
- actor
- counterparty
- intent
- transition
- current state
- World
- confidence
- evidence reference
- expected next transition
- closure
- source
- metadata

## Rules

- Confidence must be between 0 and 1.
- Terminal transitions automatically close the event.
- The model remains industry-neutral.
- No database or API change is introduced in this milestone.
