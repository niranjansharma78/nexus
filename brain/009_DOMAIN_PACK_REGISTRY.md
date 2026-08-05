# ADR-009: Domain Pack Registry

Status: Accepted  
Brain version: 0.5.0 Milestone 4

The Universal Brain must remain industry-neutral. Domain packs translate
organization and industry vocabulary into universal objects, intents and
transitions.

## Responsibilities

A domain pack may contain:

- terms
- synonyms
- object mappings
- universal transition mappings
- intents
- expected next transitions

A domain pack must not:

- change the universal transition ontology
- introduce confidential organization data into the global layer
- override explicit user or organization policy
- hardcode one industry's workflow into Nexus Core

## Resolution rule

When multiple vocabulary terms match, the longest matching phrase wins.

Examples:

- dispatch
- deployment
- shipment

All may resolve to the universal transition `transferred`.

## Current scope

Milestone 4 introduces:

- DomainMapping
- DomainPack
- DomainPackRegistry
- generic default vocabulary
- metadata listing
- explicit pack replacement controls

No database, API or live event inference is introduced yet.
