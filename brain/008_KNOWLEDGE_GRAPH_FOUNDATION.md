# ADR-008: Knowledge Graph Foundation

Status: Accepted  
Brain version: 0.5.0 Milestone 3

The Knowledge Graph is divided into three explicit layers.

## Reality
Auditable observations and immutable source-derived facts.

Examples:
- an email was received
- a payment message was observed
- a file was attached
- a meeting occurred

## Understanding
Interpretations created by Nexus.

Examples:
- a commitment exists
- two identities refer to the same organization
- an event belongs to an open communication loop

## Wisdom
Predictions, recommendations and learned patterns.

Examples:
- a response is likely overdue
- a relationship is strengthening
- a commitment may be at risk

## Rules

- Layers must remain distinguishable.
- Confidence is mandatory for every node and edge.
- Evidence references belong on relationships and observations.
- Reality must not be overwritten by later interpretation.
- Understanding and Wisdom can evolve as evidence changes.

Milestone 3 introduces only an in-memory graph. Persistent graph storage will be
added only after the model and tests are stable.
