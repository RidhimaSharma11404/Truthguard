"""
Unit tests for TruthGuard Precedence Engine
Covers all five traps + tie/abstain cases + named regression test for the Hero Refund Case.
As required by Section 7 of the Implementation Plan.
"""

from datetime import date
import pytest

from truthguard.schema import Clause, Scope, SpecificityType, Relation, RelationType
from truthguard.graph import ClauseGraph
from truthguard.precedence_engine import PrecedenceEngine, VerdictStatus


@pytest.fixture
def engine():
    return PrecedenceEngine()


def test_trap1_authority_over_recency(engine):
    """
    Trap 1: A newer FAQ (Aug 2025) cannot overrule an older board policy (Jan 2025).
    """
    board_policy = Clause(
        clause_id="BP-cl-1",
        doc_id="Refund Policy Board v1",
        doc_type="board policy",
        text="All customer cancellations receive full refunds within 7 business days.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="cancellation"
    )

    newer_faq = Clause(
        clause_id="FAQ-cl-8",
        doc_id="Customer Help FAQ",
        doc_type="FAQ",
        text="Cancellations are strictly non-refundable.",
        authority_rank=2,
        published_date=date(2025, 8, 1),
        effective_from=date(2025, 8, 1),
        specificity=SpecificityType.GENERAL,
        topic="cancellation"
    )

    verdict = engine.evaluate(
        candidates=[newer_faq, board_policy],
        as_of_date=date(2025, 8, 15)
    )

    assert verdict.status == VerdictStatus.RESOLVED
    assert verdict.winning_clause.clause_id == "BP-cl-1"
    assert verdict.winning_clause.authority_rank > newer_faq.authority_rank


def test_trap2_clause_level_supersession(engine):
    """
    Trap 2: One clause, not the whole document.
    Amending cl.4.2 does not cancel the rest of v1 (e.g. cl.4.5).
    """
    graph = ClauseGraph()

    cl_4_2 = Clause(
        clause_id="RP-v1-4.2",
        doc_id="Refund Policy v1",
        doc_type="board policy",
        text="Refund window is 7 days from transaction.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="refund_window"
    )

    cl_4_5 = Clause(
        clause_id="RP-v1-4.5",
        doc_id="Refund Policy v1",
        doc_type="board policy",
        text="Refunds must be remitted back to the original credit/debit card, never as store credits.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="payment_method"
    )

    amd_a_cl1 = Clause(
        clause_id="AMD-A-1",
        doc_id="Amendment A",
        doc_type="board policy",
        text="Refund window is amended to 14 days.",
        authority_rank=4,
        published_date=date(2025, 3, 1),
        effective_from=date(2025, 7, 1),
        relations=[Relation(type=RelationType.AMENDS, target="RP-v1-4.2")],
        specificity=SpecificityType.GENERAL,
        topic="refund_window"
    )

    graph.add_clause(cl_4_2)
    graph.add_clause(cl_4_5)
    graph.add_clause(amd_a_cl1)

    # When querying for payment method (cl.4.5) on 15 Jul 2025:
    verdict = engine.evaluate(
        candidates=[cl_4_5],
        as_of_date=date(2025, 7, 15),
        graph=graph
    )
    # cl.4.5 remains valid and in force; it was never amended!
    assert verdict.status == VerdictStatus.RESOLVED
    assert verdict.winning_clause.clause_id == "RP-v1-4.5"


def test_trap3_hero_refund_case(engine):
    """
    Named Hero Case regression test (Section 7):
    - Policy v1: cl.4.2 = 7 days (published Jan 2025, effective 1 Jan 2025)
    - Amendment A: replaces cl.4.2 with 14 days (published Mar 2025, effective 1 Jul 2025)
    - FAQ #12: published Aug 2025

    Testing:
    Asking on 20 Jun 2025 must return the 7-day rule (RP-v1-4.2).
    Asking on 2 Jul 2025 must return the 14-day rule (AMD-A-1).
    """
    cl_4_2 = Clause(
        clause_id="RP-v1-4.2",
        doc_id="Refund Policy v1",
        doc_type="board policy",
        text="Refunds allowed within 7 days from transaction date.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="refund_window"
    )

    amd_a = Clause(
        clause_id="AMD-A-1",
        doc_id="Amendment A",
        doc_type="board policy",
        text="Refunds allowed within 14 days from transaction date.",
        authority_rank=4,
        published_date=date(2025, 3, 15),
        effective_from=date(2025, 7, 1),
        relations=[Relation(type=RelationType.AMENDS, target="RP-v1-4.2")],
        specificity=SpecificityType.GENERAL,
        topic="refund_window"
    )

    faq_12 = Clause(
        clause_id="FAQ-12",
        doc_id="Support FAQ #12",
        doc_type="FAQ",
        text="Refunds allowed within 7 days, as store credit.",
        authority_rank=2,
        published_date=date(2025, 8, 1),
        effective_from=date(2025, 8, 1),
        specificity=SpecificityType.GENERAL,
        topic="refund_window"
    )

    candidates = [cl_4_2, amd_a, faq_12]

    # Test 1: Asking on 20 Jun 2025 (Amendment A is NOT yet in force, FAQ-12 is not published)
    verdict_20_jun = engine.evaluate(
        candidates=candidates,
        as_of_date=date(2025, 6, 20)
    )
    assert verdict_20_jun.status == VerdictStatus.RESOLVED
    assert verdict_20_jun.winning_clause.clause_id == "RP-v1-4.2"
    assert "7 days" in verdict_20_jun.winning_clause.text

    # Test 2: Asking on 2 Jul 2025 (Amendment A IS in force, and supersedes cl.4.2)
    verdict_2_jul = engine.evaluate(
        candidates=candidates,
        as_of_date=date(2025, 7, 2)
    )
    assert verdict_2_jul.status == VerdictStatus.RESOLVED
    assert verdict_2_jul.winning_clause.clause_id == "AMD-A-1"
    assert "14 days" in verdict_2_jul.winning_clause.text


def test_trap4_specific_over_general(engine):
    """
    Trap 4: Specific beats general.
    A regional / segment exception survives a newer general rule, unless explicitly repealed.
    """
    national_general = Clause(
        clause_id="TC-NAT-1",
        doc_id="National Tariff Terms 2025",
        doc_type="product T&C",
        text="Daily high-speed roaming data is capped at 1GB across all regions.",
        authority_rank=3,
        scope=Scope(product="prepaid", region="all", customer_segment="all"),
        published_date=date(2025, 5, 1),
        effective_from=date(2025, 5, 1),
        specificity=SpecificityType.GENERAL,
        topic="roaming_cap"
    )

    delhi_exception = Clause(
        clause_id="TC-DEL-1",
        doc_id="Delhi Student Roaming Special",
        doc_type="product T&C",
        text="Enrolled students in the Delhi National Capital Region receive 3GB daily roaming data.",
        authority_rank=3,
        scope=Scope(product="prepaid", region="Delhi", customer_segment="student"),
        published_date=date(2025, 2, 1),
        effective_from=date(2025, 2, 1),
        specificity=SpecificityType.NARROW,
        topic="roaming_cap"
    )

    # For a query with Delhi + student scope:
    query_scope = Scope(product="prepaid", region="Delhi", customer_segment="student")

    verdict = engine.evaluate(
        candidates=[national_general, delhi_exception],
        as_of_date=date(2025, 6, 1),
        customer_scope=query_scope
    )

    assert verdict.status == VerdictStatus.RESOLVED
    assert verdict.winning_clause.clause_id == "TC-DEL-1"
    assert verdict.winning_clause.specificity == SpecificityType.NARROW


def test_trap5_amendment_chains(engine):
    """
    Trap 5: Amendments of amendments.
    If Amendment B withdraws Amendment A, trace back to the right clause.
    """
    original = Clause(
        clause_id="BASE-1",
        doc_id="Broadband Plan 2024",
        doc_type="product T&C",
        text="Late fee is 5% after due date.",
        authority_rank=3,
        published_date=date(2024, 1, 1),
        effective_from=date(2024, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="late_fee"
    )

    amd_a = Clause(
        clause_id="AMD-A-FEE",
        doc_id="Amendment A",
        doc_type="product T&C",
        text="Late fee increased to 10%.",
        authority_rank=3,
        published_date=date(2024, 6, 1),
        effective_from=date(2024, 6, 1),
        relations=[Relation(type=RelationType.AMENDS, target="BASE-1")],
        specificity=SpecificityType.GENERAL,
        topic="late_fee"
    )

    amd_b = Clause(
        clause_id="AMD-B-FEE",
        doc_id="Amendment B",
        doc_type="product T&C",
        text="Amendment A is hereby rescinded and withdrawn. Late fee is reset to flat Rs. 50.",
        authority_rank=3,
        published_date=date(2024, 9, 1),
        effective_from=date(2024, 9, 1),
        relations=[
            Relation(type=RelationType.WITHDRAWS, target="AMD-A-FEE"),
            Relation(type=RelationType.AMENDS, target="BASE-1")
        ],
        specificity=SpecificityType.GENERAL,
        topic="late_fee"
    )

    verdict = engine.evaluate(
        candidates=[original, amd_a, amd_b],
        as_of_date=date(2024, 10, 1)
    )

    assert verdict.status == VerdictStatus.RESOLVED
    assert verdict.winning_clause.clause_id == "AMD-B-FEE"


def test_tie_and_abstain_case(engine):
    """
    Section 7: If more than one clause survives all six checks,
    the engine returns a tie and the system abstains, showing both sources.
    """
    doc_alpha = Clause(
        clause_id="TIE-ALPHA",
        doc_id="Carrier Interconnect Agreement A",
        doc_type="board policy",
        text="Dispute settlement SLA is 15 calendar days.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="dispute_sla"
    )

    doc_beta = Clause(
        clause_id="TIE-BETA",
        doc_id="Carrier Interconnect Agreement B",
        doc_type="board policy",
        text="Dispute settlement SLA is 30 calendar days.",
        authority_rank=4,
        published_date=date(2025, 1, 1),
        effective_from=date(2025, 1, 1),
        specificity=SpecificityType.GENERAL,
        topic="dispute_sla"
    )

    verdict = engine.evaluate(
        candidates=[doc_alpha, doc_beta],
        as_of_date=date(2025, 6, 1)
    )

    assert verdict.status == VerdictStatus.TIE_ABSTAIN
    assert len(verdict.tied_clauses) == 2
    assert {c.clause_id for c in verdict.tied_clauses} == {"TIE-ALPHA", "TIE-BETA"}
