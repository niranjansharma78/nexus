# ADR-024: Decision Engine v1

Status: Accepted
Brain version: 1.7.0 Alpha 1

The Decision Engine is standalone-first.

It accepts structured options and optionally consumes context, prediction
references, simulation references, constraints and intent.

## Architectural rules

- It must work without the complete Nexus Brain.
- Constraint-violating options cannot be recommended.
- Recommended option and chosen option remain separate.
- The human or calling product may choose a different option.
- Decisions preserve provenance and can later feed Reflection.
