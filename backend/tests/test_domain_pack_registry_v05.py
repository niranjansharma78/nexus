import pytest

from app.brain.ontology.domain_pack import DomainMapping, DomainPack
from app.brain.ontology.registry import (
    DomainPackRegistry,
    build_default_registry,
)
from app.brain.ontology.transitions import UniversalTransition


def test_generic_pack_maps_different_industries_to_same_transition():
    registry = build_default_registry()

    manufacturing = registry.resolve("Goods dispatched to the customer")
    software = registry.resolve("Release deployed to production")
    retail = registry.resolve("Order shipped to the buyer")

    assert manufacturing is not None
    assert software is not None
    assert retail is not None

    assert manufacturing[1].transition == UniversalTransition.TRANSFERRED
    assert software[1].transition == UniversalTransition.TRANSFERRED
    assert retail[1].transition == UniversalTransition.TRANSFERRED


def test_longest_matching_term_wins():
    pack = DomainPack(
        name="test",
        version="1.0",
        mappings=[
            DomainMapping(
                term="payment",
                object_kind="transaction",
                transition=UniversalTransition.REQUESTED,
                intent="settlement_request",
            ),
            DomainMapping(
                term="payment received",
                object_kind="transaction",
                transition=UniversalTransition.SETTLED,
                intent="settlement",
            ),
        ],
    )

    mapping = pack.resolve("Payment received from the customer")

    assert mapping is not None
    assert mapping.transition == UniversalTransition.SETTLED


def test_duplicate_pack_requires_explicit_replace():
    registry = DomainPackRegistry()
    pack = DomainPack(name="generic", version="1.0")

    registry.register(pack)

    with pytest.raises(ValueError):
        registry.register(pack)

    replacement = DomainPack(name="generic", version="2.0")
    registry.register(replacement, replace=True)

    assert registry.require("generic").version == "2.0"


def test_registry_can_limit_resolution_to_named_packs():
    registry = DomainPackRegistry()
    registry.register(
        DomainPack(
            name="alpha",
            version="1.0",
            mappings=[
                DomainMapping(
                    term="alpha term",
                    object_kind="event",
                    transition=UniversalTransition.OBSERVED,
                    intent="alpha",
                )
            ],
        )
    )
    registry.register(
        DomainPack(
            name="beta",
            version="1.0",
            mappings=[
                DomainMapping(
                    term="beta term",
                    object_kind="event",
                    transition=UniversalTransition.OBSERVED,
                    intent="beta",
                )
            ],
        )
    )

    assert registry.resolve("beta term", pack_names=["alpha"]) is None

    result = registry.resolve("beta term", pack_names=["beta"])
    assert result is not None
    assert result[0].name == "beta"


def test_registry_lists_metadata_without_exposing_internal_objects():
    registry = build_default_registry()

    items = registry.list()

    assert items
    assert items[0]["name"] == "generic"
    assert items[0]["mapping_count"] > 0


def test_invalid_mapping_is_rejected():
    with pytest.raises(ValueError):
        DomainMapping(
            term="",
            object_kind="event",
            transition=UniversalTransition.OBSERVED,
            intent="observation",
        )
