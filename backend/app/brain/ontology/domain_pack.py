from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.brain.ontology.transitions import UniversalTransition


@dataclass(frozen=True, slots=True)
class DomainMapping:
    term: str
    object_kind: str
    transition: UniversalTransition
    intent: str
    expected_next: UniversalTransition | None = None
    synonyms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.term.strip():
            raise ValueError("Domain term is required")
        if not self.object_kind.strip():
            raise ValueError("Object kind is required")
        if not self.intent.strip():
            raise ValueError("Intent is required")

    @property
    def all_terms(self) -> tuple[str, ...]:
        return (self.term, *self.synonyms)


def _contains_term(text: str, term: str) -> bool:
    normalized = term.strip()
    if not normalized:
        return False

    pattern = rf"(?<!\w){re.escape(normalized)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


@dataclass(slots=True)
class DomainPack:
    name: str
    version: str
    mappings: list[DomainMapping] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Domain pack name is required")
        if not self.version.strip():
            raise ValueError("Domain pack version is required")

    def resolve(self, text: str) -> DomainMapping | None:
        matches: list[tuple[int, DomainMapping]] = []

        for mapping in self.mappings:
            for term in mapping.all_terms:
                if _contains_term(text, term):
                    matches.append((len(term.strip()), mapping))

        if not matches:
            return None

        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]