# ADR-018: Universal Perception Framework v1

Status: Accepted  
Brain version: 1.1.0 Alpha 1

The Brain never reasons directly over external systems. Sensors produce
Observations. Observations are normalized into Universal Evidence.

## Core elements

- NexusSensor
- SensorRegistry
- Observation
- UniversalEvidence
- EvidenceNormalizer
- EvidenceRepository
- PerceptionPipeline
- SensorHealth

## Rules

- Sensors must remain independent of reasoning.
- Evidence must preserve source, timestamp and confidence.
- Replayed observations must be deduplicated.
- Sensor failure must not stop other sensors.
- Health reporting is mandatory.
- Call transcription is parked for future Communication Intelligence.
