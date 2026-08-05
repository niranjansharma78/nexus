from __future__ import annotations

from app.brain.ontology.domain_pack import (
    DomainMapping,
    DomainPack,
    _contains_term,
)
from app.brain.ontology.transitions import UniversalTransition


class DomainPackRegistry:
    def __init__(self) -> None:
        self._packs: dict[str, DomainPack] = {}

    def register(
        self,
        pack: DomainPack,
        *,
        replace: bool = False,
    ) -> DomainPack:
        key = pack.name.casefold()

        if key in self._packs and not replace:
            raise ValueError(
                f"Domain pack already registered: {pack.name}"
            )

        self._packs[key] = pack
        return pack

    def get(self, name: str) -> DomainPack | None:
        return self._packs.get(name.casefold())

    def require(self, name: str) -> DomainPack:
        pack = self.get(name)

        if pack is None:
            raise KeyError(f"Domain pack not found: {name}")

        return pack

    def resolve(
        self,
        text: str,
        *,
        pack_names: list[str] | None = None,
    ) -> tuple[DomainPack, DomainMapping] | None:
        packs = (
            [self.require(name) for name in pack_names]
            if pack_names is not None
            else list(self._packs.values())
        )

        matches: list[
            tuple[int, DomainPack, DomainMapping]
        ] = []

        for pack in packs:
            mapping = pack.resolve(text)

            if mapping is None:
                continue

            longest_term = max(
                (
                    len(term.strip())
                    for term in mapping.all_terms
                    if _contains_term(text, term)
                ),
                default=0,
            )

            matches.append(
                (
                    longest_term,
                    pack,
                    mapping,
                )
            )

        if not matches:
            return None

        matches.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        _, pack, mapping = matches[0]

        return pack, mapping

    def list(self) -> list[dict[str, object]]:
        return [
            {
                "name": pack.name,
                "version": pack.version,
                "mapping_count": len(pack.mappings),
            }
            for pack in sorted(
                self._packs.values(),
                key=lambda item: item.name.casefold(),
            )
        ]


def build_default_registry() -> DomainPackRegistry:
    registry = DomainPackRegistry()

    registry.register(
        DomainPack(
            name="generic",
            version="0.5.0",
            mappings=[
                DomainMapping(
                    term="request",
                    object_kind="commitment",
                    transition=UniversalTransition.REQUESTED,
                    intent="request",
                    expected_next=UniversalTransition.COMMITTED,
                    synonyms=(
                        "requested",
                        "requirement",
                        "enquiry",
                        "asked for",
                    ),
                ),
                DomainMapping(
                    term="approval",
                    object_kind="commitment",
                    transition=UniversalTransition.APPROVED,
                    intent="approval",
                    expected_next=UniversalTransition.STARTED,
                    synonyms=(
                        "approved",
                        "authorized",
                    ),
                ),
                DomainMapping(
                    term="started",
                    object_kind="work",
                    transition=UniversalTransition.STARTED,
                    intent="execution",
                    expected_next=UniversalTransition.PROGRESSED,
                    synonyms=(
                        "commenced",
                        "initiated",
                        "underway",
                    ),
                ),
                DomainMapping(
                    term="completed",
                    object_kind="work",
                    transition=UniversalTransition.COMPLETED,
                    intent="completion",
                    expected_next=UniversalTransition.ACCEPTED,
                    synonyms=(
                        "finished",
                        "done",
                    ),
                ),
                DomainMapping(
                    term="transferred",
                    object_kind="resource",
                    transition=UniversalTransition.TRANSFERRED,
                    intent="transfer",
                    expected_next=UniversalTransition.RECEIVED,
                    synonyms=(
                        "sent",
                        "shipped",
                        "dispatched",
                        "deployed",
                        "released",
                    ),
                ),
                DomainMapping(
                    term="received",
                    object_kind="resource",
                    transition=UniversalTransition.RECEIVED,
                    intent="receipt",
                    expected_next=UniversalTransition.ACCEPTED,
                    synonyms=(
                        "delivered",
                        "acknowledged",
                        "receipt confirmed",
                    ),
                ),
                DomainMapping(
                    term="accepted",
                    object_kind="outcome",
                    transition=UniversalTransition.ACCEPTED,
                    intent="acceptance",
                    expected_next=UniversalTransition.CLOSED,
                    synonyms=(
                        "approved by customer",
                        "signed off",
                    ),
                ),
                DomainMapping(
                    term="payment received",
                    object_kind="transaction",
                    transition=UniversalTransition.SETTLED,
                    intent="settlement",
                    expected_next=UniversalTransition.CLOSED,
                    synonyms=(
                        "paid",
                        "settled",
                        "credited",
                    ),
                ),
                DomainMapping(
                    term="failed",
                    object_kind="event",
                    transition=UniversalTransition.FAILED,
                    intent="exception",
                    expected_next=UniversalTransition.ESCALATED,
                    synonyms=(
                        "rejected",
                        "bounce",
                        "error",
                    ),
                ),
                DomainMapping(
                    term="cancelled",
                    object_kind="commitment",
                    transition=UniversalTransition.CANCELLED,
                    intent="cancellation",
                    expected_next=UniversalTransition.CLOSED,
                    synonyms=(
                        "canceled",
                        "withdrawn",
                    ),
                ),
            ],
        )
    )

    return registry


DEFAULT_DOMAIN_PACK_REGISTRY = build_default_registry()