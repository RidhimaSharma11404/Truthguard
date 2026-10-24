"""
TruthGuard Clause Graph Tests
Verifies:
1. Graph building and relation indexing
2. Dangling link detection and validation
3. Supersession and withdrawal chain tracing
"""

from datetime import date
import pytest
from truthguard.schema import Clause, Relation, RelationType, SpecificityType
from truthguard.graph import ClauseGraph


def test_graph_validation_catches_dangling_link():
    graph = ClauseGraph()
    clause_with_bad_target = Clause(
        clause_id="TEST-AMD-1",
        doc_id="Amendment Test",
        doc_type="board policy",
        text="Amends a non-existent clause.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        relations=[Relation(type=RelationType.AMENDS, target="DOES-NOT-EXIST")]
    )
    graph.add_clause(clause_with_bad_target)
    errors = graph.validate_graph()
    assert len(errors) == 1
    assert "DOES-NOT-EXIST" in errors[0]


def test_graph_chain_tracing():
    graph = ClauseGraph()
    c1 = Clause(
        clause_id="V1-cl1",
        doc_id="Base Policy",
        doc_type="board policy",
        text="Base fee is 5%.",
        authority_rank=4,
        published_date=date(2024, 1, 1),
        effective_from=date(2024, 1, 1),
    )
    c2 = Clause(
        clause_id="V2-cl1",
        doc_id="Amendment 1",
        doc_type="board policy",
        text="Fee is 10%.",
        authority_rank=4,
        published_date=date(2024, 6, 1),
        effective_from=date(2024, 6, 1),
        relations=[Relation(type=RelationType.AMENDS, target="V1-cl1")]
    )
    c3 = Clause(
        clause_id="V3-cl1",
        doc_id="Amendment 2",
        doc_type="board policy",
        text="Fee is flat Rs. 50.",
        authority_rank=4,
        published_date=date(2024, 9, 1),
        effective_from=date(2024, 9, 1),
        relations=[
            Relation(type=RelationType.WITHDRAWS, target="V2-cl1"),
            Relation(type=RelationType.AMENDS, target="V1-cl1")
        ]
    )

    graph.add_clause(c1)
    graph.add_clause(c2)
    graph.add_clause(c3)
    graph.rebuild_edges()

    assert len(graph.validate_graph()) == 0

    # Test withdrawal
    assert graph.is_withdrawn("V2-cl1", as_of_date=date(2024, 10, 1)) is True
    assert graph.is_withdrawn("V1-cl1", as_of_date=date(2024, 10, 1)) is False

    # Test supersession on 2024-07-01: V1-cl1 superseded by V2-cl1
    is_sup, sup_id = graph.is_superseded("V1-cl1", as_of_date=date(2024, 7, 1))
    assert is_sup is True
    assert sup_id == "V2-cl1"
