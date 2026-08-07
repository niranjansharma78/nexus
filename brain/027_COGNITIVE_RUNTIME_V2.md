# ADR-027: Cognitive Runtime v2

Status: Accepted
Brain version: 2.0.0 Alpha 1

Runtime v2 turns the Cognitive Orchestrator into a triggerable operating layer.

## Supported triggers

- manual
- evidence
- event
- schedule

## Safety boundary

Runtime v2 does not execute consequential actions.

It may compose Context, Prediction, Simulation, Decision and Planning, but
execution remains disabled. High-impact Worlds and generated plans require
human approval.

This keeps cognition separate from action while the system is still evolving.
