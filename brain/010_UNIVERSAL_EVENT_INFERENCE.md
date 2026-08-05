# ADR-010: Universal Event Inference

Status: Accepted  
Brain version: 0.5.0 Milestone 5

Milestone 5 connects the Domain Pack Registry to the Universal Event Model.

## Input

Event inference accepts:

- title
- summary
- source
- World
- actor
- counterparty
- evidence reference
- confidence
- money and quantity
- importance
- organization
- optional domain-pack restriction
- metadata

## Output

Inference returns:

- the canonical UniversalEvent
- whether vocabulary matched
- which pack matched
- which primary term matched

## Fallback rule

Unknown content is never forced into a specific interpretation.

It becomes:

- object kind: `event`
- intent: `observation`
- transition: `observed`
- no expected next transition

This preserves honesty and prevents false certainty.

## Separation rule

This milestone performs only in-memory inference.

It does not:

- write to the database
- expose new API routes
- automatically process live evidence
- change existing dashboard behavior

Persistence and live integration will follow only after inference remains stable.
