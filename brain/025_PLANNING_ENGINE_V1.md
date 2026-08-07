# ADR-025: Planning Engine v1

Status: Accepted
Brain version: 1.8.0 Alpha 1

The Planning Engine is standalone-first.

## Capabilities

- dependency-aware task graphs
- readiness and blocked states
- plan progress
- critical path
- persistent plans
- decision and simulation references
- replanning signal

## Rules

- Plans must work without Nexus Runtime.
- Tasks may reference owners but execution is separate.
- Circular dependencies are rejected.
- Planning does not silently execute actions.
- Approved decisions can be linked without making Decision Engine mandatory.
