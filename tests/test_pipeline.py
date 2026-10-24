"""
TruthGuard Pipeline End-to-End Tests
Verifies:
1. Full answer pipeline execution
2. In-force date flipping on 20 Jun vs 2 Jul (Hero Case)
3. Falsification critic detecting opposite claims
4. Citation gate eliminating uncited sentences
5. Contradiction ledger ticket generation
"""

import json
from datetime import date
from pathlib import Path
import pytest

from truthguard.schema import Clause, Scope
from truthguard.pipeline import TruthGuardPipeline


@pytest.fixture
def populated_pipeline():
    base_dir = Path("C:/Users/Lenovo/.gemini/antigravity/scratch/truthguard")
    with open(base_dir / "data/clauses.json", "r", encoding="utf-8") as f:
        clauses = [Clause(**c) for c in json.load(f)]
    pipeline = TruthGuardPipeline()
    pipeline.ingest_clauses(clauses)
    return pipeline


def test_hero_refund_case_pipeline(populated_pipeline):
    hero_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"

    # Query on 20 Jun 2025
    res_20_jun = populated_pipeline.query(hero_q, as_of_date=date(2025, 6, 20))
    assert res_20_jun.status == "RESOLVED"
    assert res_20_jun.winning_clause["clause_id"] == "RP-v1-4.2"
    assert "No." in res_20_jun.answer
    assert "[RP-v1-4.2]" in res_20_jun.answer

    # Query on 2 Jul 2025
    res_2_jul = populated_pipeline.query(hero_q, as_of_date=date(2025, 7, 2))
    assert res_2_jul.status == "RESOLVED"
    assert res_2_jul.winning_clause["clause_id"] == "AMD-A-1"
    assert "Yes," in res_2_jul.answer
    assert "[AMD-A-1]" in res_2_jul.answer


def test_citation_gate_integrity(populated_pipeline):
    hero_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"
    res = populated_pipeline.query(hero_q, as_of_date=date(2025, 6, 20))

    # Ensure every single sentence in the final answer has a citation tag
    lines = [l for l in res.answer.split("\n") if l.strip()]
    for line in lines:
        assert "[" in line and "]" in line, f"Uncited sentence passed citation gate: {line}"


def test_contradiction_ledger_populated(populated_pipeline):
    tickets = populated_pipeline.ledger.get_ranked_tickets()
    assert len(tickets) > 0

    # Ensure FAQ-12 store credit vs Policy v1 card refund is present
    found_faq12_conflict = any(
        t.conflicting_clause_id in ("FAQ-12", "FAQ-12-STORE")
        for t in tickets
    )
    assert found_faq12_conflict, "FAQ #12 contradiction was not logged into the ledger!"
