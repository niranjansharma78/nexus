import pytest

from app.brain.graph.event_mapper import map_event_to_graph
from app.brain.graph.models import GraphEdge, GraphNode, KnowledgeLayer
from app.brain.graph.store import InMemoryKnowledgeGraph
from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition


def test_graph_rejects_edges_with_missing_nodes():
    graph = InMemoryKnowledgeGraph()
    edge = GraphEdge(
        source_id="missing-a",
        target_id="missing-b",
        relation="related_to",
        layer=KnowledgeLayer.REALITY,
        confidence=1.0,
    )

    with pytest.raises(ValueError):
        graph.add_edge(edge)


def test_graph_adds_nodes_edges_and_neighbors():
    graph = InMemoryKnowledgeGraph()
    person = graph.add_node(
        GraphNode(
            kind="person",
            label="A",
            layer=KnowledgeLayer.REALITY,
            confidence=1.0,
        )
    )
    organization = graph.add_node(
        GraphNode(
            kind="organization",
            label="B",
            layer=KnowledgeLayer.REALITY,
            confidence=0.9,
        )
    )
    graph.add_edge(
        GraphEdge(
            source_id=person.node_id,
            target_id=organization.node_id,
            relation="works_with",
            layer=KnowledgeLayer.UNDERSTANDING,
            confidence=0.8,
        )
    )

    neighbors = graph.neighbors(person.node_id, relation="works_with")

    assert [node.label for node in neighbors] == ["B"]
    assert graph.stats()["node_count"] == 2
    assert graph.stats()["edge_count"] == 1


def test_layers_are_kept_separate():
    graph = InMemoryKnowledgeGraph()
    graph.add_node(
        GraphNode(
            kind="event",
            label="Observed email",
            layer=KnowledgeLayer.REALITY,
            confidence=1.0,
        )
    )
    graph.add_node(
        GraphNode(
            kind="commitment",
            label="Likely commitment",
            layer=KnowledgeLayer.UNDERSTANDING,
            confidence=0.7,
        )
    )
    graph.add_node(
        GraphNode(
            kind="prediction",
            label="Possible delay",
            layer=KnowledgeLayer.WISDOM,
            confidence=0.6,
        )
    )

    assert len(graph.nodes(layer=KnowledgeLayer.REALITY)) == 1
    assert len(graph.nodes(layer=KnowledgeLayer.UNDERSTANDING)) == 1
    assert len(graph.nodes(layer=KnowledgeLayer.WISDOM)) == 1


def test_universal_event_maps_to_reality_graph():
    graph = InMemoryKnowledgeGraph()
    event = UniversalEvent(
        actor=UniversalObjectRef(kind="organization", label="Sender"),
        counterparty=UniversalObjectRef(kind="organization", label="Receiver"),
        object=UniversalObjectRef(kind="commitment", label="Example request"),
        intent="request",
        transition=UniversalTransition.REQUESTED,
        state="requested",
        world="business",
        confidence=0.92,
        source="email",
        evidence_id=42,
    )

    mapped = map_event_to_graph(graph, event)

    assert "event_node_id" in mapped
    assert "object_node_id" in mapped
    assert "actor_node_id" in mapped
    assert "counterparty_node_id" in mapped
    assert graph.stats()["node_count"] == 4
    assert graph.stats()["edge_count"] == 3
    assert len(graph.nodes(layer=KnowledgeLayer.REALITY)) == 4


def test_node_and_edge_confidence_are_validated():
    with pytest.raises(ValueError):
        GraphNode(
            kind="event",
            label="Invalid",
            layer=KnowledgeLayer.REALITY,
            confidence=1.2,
        )

    with pytest.raises(ValueError):
        GraphEdge(
            source_id="a",
            target_id="b",
            relation="related_to",
            layer=KnowledgeLayer.REALITY,
            confidence=-0.1,
        )
