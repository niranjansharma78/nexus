from __future__ import annotations

import hashlib
import json

from .models import Observation, UniversalEvidence


class EvidenceNormalizer:
    @staticmethod
    def fingerprint(observation: Observation) -> str:
        canonical = json.dumps(
            {
                "sensor_id": observation.sensor_id,
                "source": observation.source,
                "observed_at": observation.observed_at,
                "raw_payload": observation.raw_payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def normalize(self, observation: Observation) -> UniversalEvidence:
        payload = dict(observation.raw_payload)
        evidence_type = str(
            payload.get("evidence_type")
            or payload.get("type")
            or "observation"
        )

        return UniversalEvidence(
            connector=observation.sensor_id,
            evidence_type=evidence_type,
            observed_at=observation.observed_at,
            source=observation.source,
            author=payload.get("author"),
            payload=payload,
            attachments=tuple(payload.get("attachments") or ()),
            metadata={
                **observation.metadata,
                "observation_id": observation.observation_id,
            },
            confidence=observation.confidence,
            fingerprint=self.fingerprint(observation),
        )
