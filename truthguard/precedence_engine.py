"""
TruthGuard Precedence Engine
Pure deterministic code with zero LLM calls.
Implements the 6-step precedence checks in the exact order specified in Section 7 of the Implementation Plan:
1. Scope
2. In force
3. Supersession
4. Authority
5. Specificity
6. Recency

Generates a step-by-step audit trace for full transparency.
"""

from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from pydantic import BaseModel, Field

from truthguard.schema import Clause, Scope, SpecificityType, DEFAULT_AUTHORITY_TABLE
from truthguard.graph import ClauseGraph


class VerdictStatus(str, Enum):
    RESOLVED = "RESOLVED"
    TIE_ABSTAIN = "TIE_ABSTAIN"
    NO_APPLICABLE_CLAUSE = "NO_APPLICABLE_CLAUSE"


class StepAudit(BaseModel):
    step_number: int
    step_name: str
    description: str
    surviving_clause_ids: List[str]
    eliminated: List[Dict[str, str]] = Field(default_factory=list)  # {"clause_id": ..., "reason": ...}


class EngineVerdict(BaseModel):
    status: VerdictStatus
    winning_clause: Optional[Clause] = None
    tied_clauses: List[Clause] = Field(default_factory=list)
    trace: List[StepAudit] = Field(default_factory=list)
    summary_explanation: str = ""


class PrecedenceEngine:
    def __init__(self, authority_table: Optional[Dict[str, int]] = None):
        self.authority_table = authority_table or DEFAULT_AUTHORITY_TABLE

    def evaluate(
        self,
        candidates: List[Clause],
        as_of_date: date,
        customer_scope: Optional[Scope] = None,
        graph: Optional[ClauseGraph] = None,
    ) -> EngineVerdict:
        """
        Runs the 6 deterministic checks in strict order:
        1. Scope: drop clauses that do not cover product, region or customer.
        2. In force: drop clauses not effective on as-of date.
        3. Supersession: follow amends and withdraws chains, remove replaced clauses.
        4. Authority: keep highest-ranked source (regulation > board policy > product T&C > FAQ > email).
        5. Specificity: narrower rule beats general one.
        6. Recency: newer wins only between otherwise equal clauses.
        """
        trace: List[StepAudit] = []
        current: List[Clause] = list(candidates)

        if not current:
            return EngineVerdict(
                status=VerdictStatus.NO_APPLICABLE_CLAUSE,
                summary_explanation="No candidate clauses were provided to the precedence engine."
            )

        # -------------------------------------------------------------
        # STEP 1: SCOPE
        # Drop clauses that do not cover the product, region or customer
        # -------------------------------------------------------------
        scope_eliminated = []
        scope_survivors = []
        for c in current:
            if c.scope.matches(customer_scope):
                scope_survivors.append(c)
            else:
                scope_eliminated.append({
                    "clause_id": c.clause_id,
                    "reason": f"Scope mismatch: clause scope (product={c.scope.product}, region={c.scope.region}, segment={c.scope.customer_segment}) does not match query scope (product={customer_scope.product if customer_scope else 'all'}, region={customer_scope.region if customer_scope else 'all'}, segment={customer_scope.customer_segment if customer_scope else 'all'})"
                })
        
        trace.append(StepAudit(
            step_number=1,
            step_name="Scope Check",
            description="Drop clauses that do not cover the requested product, region or customer segment.",
            surviving_clause_ids=[c.clause_id for c in scope_survivors],
            eliminated=scope_eliminated
        ))
        current = scope_survivors

        if not current:
            return EngineVerdict(
                status=VerdictStatus.NO_APPLICABLE_CLAUSE,
                trace=trace,
                summary_explanation="All candidate clauses were eliminated at Step 1 (Scope Check)."
            )

        # -------------------------------------------------------------
        # STEP 2: IN FORCE
        # Drop clauses not effective on the as-of date
        # -------------------------------------------------------------
        in_force_eliminated = []
        in_force_survivors = []
        for c in current:
            if c.is_in_force_on(as_of_date):
                in_force_survivors.append(c)
            else:
                if as_of_date < c.effective_from:
                    reason = f"Not yet in force on {as_of_date}: effective from {c.effective_from} (published on {c.published_date})"
                else:
                    reason = f"No longer in force on {as_of_date}: expired on {c.effective_to}"
                in_force_eliminated.append({
                    "clause_id": c.clause_id,
                    "reason": reason
                })

        trace.append(StepAudit(
            step_number=2,
            step_name="In-Force Date Check",
            description=f"Drop clauses not effective on query as-of date ({as_of_date}). Checks effective_from and effective_to.",
            surviving_clause_ids=[c.clause_id for c in in_force_survivors],
            eliminated=in_force_eliminated
        ))
        current = in_force_survivors

        if not current:
            return EngineVerdict(
                status=VerdictStatus.NO_APPLICABLE_CLAUSE,
                trace=trace,
                summary_explanation=f"All candidate clauses were eliminated at Step 2 (In-Force Check) for as-of date {as_of_date}."
            )

        # -------------------------------------------------------------
        # STEP 3: SUPERSESSION
        # Follow amends and withdraws chains clause by clause, and remove replaced clauses
        # -------------------------------------------------------------
        supersession_eliminated = []
        supersession_survivors = []

        # Check among current candidates and via graph
        for c in current:
            is_superseded = False
            superseded_reason = ""

            # Check if any other clause in candidates amends or withdraws this clause
            for other in candidates:
                if other.clause_id == c.clause_id:
                    continue
                # If other is active on as_of_date and explicitly amends/withdraws c
                if other.is_in_force_on(as_of_date):
                    for rel in other.relations:
                        if rel.target == c.clause_id:
                            if rel.type.value in ("amends", "withdraws", "supersedes"):
                                is_superseded = True
                                superseded_reason = f"Superseded/withdrawn by clause {other.clause_id} ({rel.type.value} link in {other.doc_id})"
                                break
                if is_superseded:
                    break

            # If not found directly in candidates, check graph if provided
            if not is_superseded and graph:
                sup, sup_id = graph.is_superseded(c.clause_id, as_of_date)
                if sup:
                    is_superseded = True
                    superseded_reason = f"Superseded/withdrawn in clause graph by {sup_id}"

            if is_superseded:
                supersession_eliminated.append({
                    "clause_id": c.clause_id,
                    "reason": superseded_reason
                })
            else:
                supersession_survivors.append(c)

        trace.append(StepAudit(
            step_number=3,
            step_name="Supersession & Amendment Trail",
            description="Follow amends and withdraws chains clause by clause; drop clauses replaced by active revisions.",
            surviving_clause_ids=[c.clause_id for c in supersession_survivors],
            eliminated=supersession_eliminated
        ))
        current = supersession_survivors

        if not current:
            return EngineVerdict(
                status=VerdictStatus.NO_APPLICABLE_CLAUSE,
                trace=trace,
                summary_explanation="All candidate clauses were superseded or withdrawn."
            )

        if len(current) == 1:
            return EngineVerdict(
                status=VerdictStatus.RESOLVED,
                winning_clause=current[0],
                trace=trace,
                summary_explanation=f"Clause {current[0].clause_id} uniquely survived through Step 3 (Supersession)."
            )

        # -------------------------------------------------------------
        # STEP 4: AUTHORITY
        # Keep the highest-ranked source (regulation > board policy > product T&C > FAQ > email)
        # -------------------------------------------------------------
        # Note: Decision settled early in spec: Authority beats Specificity when an FAQ conflicts with board policy.
        max_authority = max(c.authority_rank for c in current)
        authority_survivors = [c for c in current if c.authority_rank == max_authority]
        authority_eliminated = [
            {
                "clause_id": c.clause_id,
                "reason": f"Lower authority rank ({c.authority_rank} - {c.doc_type}) than highest surviving rank ({max_authority})"
            }
            for c in current if c.authority_rank < max_authority
        ]

        trace.append(StepAudit(
            step_number=4,
            step_name="Authority Hierarchy",
            description="Keep highest-ranked source (Regulation > Board Policy > Product T&C > FAQ > Email).",
            surviving_clause_ids=[c.clause_id for c in authority_survivors],
            eliminated=authority_eliminated
        ))
        current = authority_survivors

        if len(current) == 1:
            return EngineVerdict(
                status=VerdictStatus.RESOLVED,
                winning_clause=current[0],
                trace=trace,
                summary_explanation=f"Clause {current[0].clause_id} won by superior authority rank ({current[0].authority_rank} vs {max_authority})."
            )

        # -------------------------------------------------------------
        # STEP 5: SPECIFICITY
        # The narrower rule beats the general one (narrow > general)
        # -------------------------------------------------------------
        has_narrow = any(c.specificity == SpecificityType.NARROW for c in current)
        has_general = any(c.specificity == SpecificityType.GENERAL for c in current)

        if has_narrow and has_general:
            specificity_survivors = [c for c in current if c.specificity == SpecificityType.NARROW]
            specificity_eliminated = [
                {
                    "clause_id": c.clause_id,
                    "reason": "General rule beaten by specific / narrow regional or segment exception."
                }
                for c in current if c.specificity == SpecificityType.GENERAL
            ]
        else:
            specificity_survivors = current
            specificity_eliminated = []

        trace.append(StepAudit(
            step_number=5,
            step_name="Specificity Check",
            description="Narrow regional or segment exception beats general rule unless repealed.",
            surviving_clause_ids=[c.clause_id for c in specificity_survivors],
            eliminated=specificity_eliminated
        ))
        current = specificity_survivors

        if len(current) == 1:
            return EngineVerdict(
                status=VerdictStatus.RESOLVED,
                winning_clause=current[0],
                trace=trace,
                summary_explanation=f"Clause {current[0].clause_id} won as a specific/narrow exception."
            )

        # -------------------------------------------------------------
        # STEP 6: RECENCY
        # Newer wins only between otherwise equal clauses
        # -------------------------------------------------------------
        # Determine recency based on effective_from date (or published_date if identical)
        max_effective_date = max(c.effective_from for c in current)
        recency_candidates = [c for c in current if c.effective_from == max_effective_date]

        if len(recency_candidates) > 1:
            max_pub_date = max(c.published_date for c in recency_candidates)
            recency_survivors = [c for c in recency_candidates if c.published_date == max_pub_date]
        else:
            recency_survivors = recency_candidates

        recency_eliminated = [
            {
                "clause_id": c.clause_id,
                "reason": f"Older clause (effective {c.effective_from}, published {c.published_date}) superseded by newer equal clause."
            }
            for c in current if c not in recency_survivors
        ]

        trace.append(StepAudit(
            step_number=6,
            step_name="Recency Tie-Breaker",
            description="Newer wins only between otherwise equal clauses.",
            surviving_clause_ids=[c.clause_id for c in recency_survivors],
            eliminated=recency_eliminated
        ))
        current = recency_survivors

        # -------------------------------------------------------------
        # FINAL VERDICT: Single Winner vs Tie & Abstain
        # -------------------------------------------------------------
        if len(current) == 1:
            return EngineVerdict(
                status=VerdictStatus.RESOLVED,
                winning_clause=current[0],
                trace=trace,
                summary_explanation=f"Clause {current[0].clause_id} resolved as the valid prevailing clause on {as_of_date}."
            )
        else:
            # More than one clause survived all 6 checks!
            # Section 7: "If more than one clause survives all six checks, the engine returns a tie and the system abstains, showing both sources."
            return EngineVerdict(
                status=VerdictStatus.TIE_ABSTAIN,
                tied_clauses=current,
                trace=trace,
                summary_explanation=f"Genuine irreconcilable conflict between {len(current)} clauses with identical authority, specificity, and recency. TruthGuard abstains and presents both sources."
            )
