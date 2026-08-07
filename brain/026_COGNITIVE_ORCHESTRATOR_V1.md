# ADR-026: Cognitive Orchestrator v1

Status: Accepted
Brain version: 1.9.0 Alpha 1

The Cognitive Orchestrator composes independent Nexus cognitive engines.

## Core rule

The orchestrator depends on engines. Engines never depend on the orchestrator.

This preserves:
- standalone SDK use,
- standalone REST use,
- Nexus LI composition,
- independent commercial products.

## v1 orchestration stages

- Context
- Prediction
- Simulation
- Decision
- Planning

Each stage is optional and failure-isolated.
