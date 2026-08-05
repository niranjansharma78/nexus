# ADR-006: Universal Transition Ontology

Status: Accepted  
Brain version: 0.5.0 Milestone 1

Nexus Core uses a compact, industry-neutral transition vocabulary:

- observed
- requested
- proposed
- committed
- approved
- scheduled
- started
- progressed
- completed
- transferred
- received
- accepted
- settled
- rejected
- failed
- cancelled
- expired
- escalated
- closed

Industry-specific words such as dispatch, deployment, discharge, shipment,
approval, payment and closure must map into this ontology through domain or
organization vocabularies.

Terminal transitions are:

- settled
- rejected
- failed
- cancelled
- expired
- closed

This milestone intentionally adds no database schema, API routes or event
inference. It establishes only the stable transition foundation.
