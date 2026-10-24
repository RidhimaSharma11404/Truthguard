"""
TruthGuard Conflict Fuzzer
Section 8: "A script that injects new conflicting versions of existing clauses
and checks that TruthGuard still resolves them. This supports the claim in the deck
that new conflicts can be generated on demand."
"""

from __future__ import annotations
import random
import uuid
from datetime import date, timedelta
from typing import Dict, List, Any

from truthguard.schema import Clause, Scope, SpecificityType, Relation, RelationType
from truthguard.pipeline import TruthGuardPipeline


class ConflictFuzzer:
    def __init__(self, pipeline: TruthGuardPipeline):
        self.pipeline = pipeline

    def run_fuzz_cycle(self, num_injections: int = 5) -> List[Dict[str, Any]]:
        """
        Synthesizes dynamic conflicting clauses, injects them into the corpus/pipeline,
        runs test queries, and evaluates how TruthGuard handles the newly injected conflicts.
        """
        results = []
        base_topics = ["refund_window", "roaming_limit", "late_fee", "theatrical_holdback", "porting_fee"]

        for i in range(num_injections):
            fuzz_id = f"FUZZ-{uuid.uuid4().hex[:6].upper()}"
            topic = random.choice(base_topics)
            fuzz_strategy = random.choice([
                "unauthorized_email",
                "future_amendment",
                "narrow_exception",
                "contradictory_faq"
            ])

            if fuzz_strategy == "unauthorized_email":
                # Plant a support email claiming 60 days
                fuzzed_clause = Clause(
                    clause_id=f"EMAIL-{fuzz_id}",
                    doc_id=f"Rogue Agent Email {fuzz_id}",
                    doc_type="support email",
                    text=f"Support rep promises full discretionary waiver with zero penalty for topic {topic}.",
                    authority_rank=1,
                    published_date=date(2025, 11, 1),
                    effective_from=date(2025, 11, 1),
                    specificity=SpecificityType.GENERAL,
                    topic=topic
                )
                query = f"Can a customer get a discretionary waiver for {topic.replace('_', ' ')} based on agent email?"
                as_of = date(2025, 11, 15)

            elif fuzz_strategy == "future_amendment":
                # Plant amendment published now, but effective in 2026
                target_clause = "RP-v1-4.2" if topic == "refund_window" else "FIBER-BASE-LATEFEE"
                fuzzed_clause = Clause(
                    clause_id=f"AMD-FUTURE-{fuzz_id}",
                    doc_id=f"Future Board Amendment {fuzz_id}",
                    doc_type="board policy",
                    text=f"Future revised terms for {topic}: valid window expanded to 60 days.",
                    authority_rank=4,
                    published_date=date(2025, 10, 1),
                    effective_from=date(2026, 6, 1),  # Far future!
                    relations=[Relation(type=RelationType.AMENDS, target=target_clause)],
                    specificity=SpecificityType.GENERAL,
                    topic=topic
                )
                query = f"What is the valid policy window for {topic.replace('_', ' ')} on 15 Oct 2025?"
                as_of = date(2025, 10, 15)

            elif fuzz_strategy == "narrow_exception":
                fuzzed_clause = Clause(
                    clause_id=f"NARROW-{fuzz_id}",
                    doc_id=f"Goa Tourist Special Addendum {fuzz_id}",
                    doc_type="product T&C",
                    text=f"Special roaming allowance exception: verified tourists in Goa receive 5GB high-speed roaming.",
                    authority_rank=3,
                    scope=Scope(product="prepaid", region="Goa", customer_segment="tourist"),
                    published_date=date(2025, 4, 1),
                    effective_from=date(2025, 4, 1),
                    specificity=SpecificityType.NARROW,
                    topic="roaming_limit"
                )
                query = "What is the roaming data limit for a prepaid tourist in Goa?"
                as_of = date(2025, 8, 1)

            else:  # contradictory_faq
                fuzzed_clause = Clause(
                    clause_id=f"FAQ-ROUTINE-{fuzz_id}",
                    doc_id=f"Customer Portal Helper FAQ {fuzz_id}",
                    doc_type="FAQ",
                    text=f"Customer help note: full refund window is extended to 60 days for all users.",
                    authority_rank=2,
                    published_date=date(2025, 9, 1),
                    effective_from=date(2025, 9, 1),
                    specificity=SpecificityType.GENERAL,
                    topic="refund_window"
                )
                query = "What is the customer recharge refund eligibility window?"
                as_of = date(2025, 9, 15)

            # Ingest temporarily
            prev_clauses = list(self.pipeline.all_clauses)
            self.pipeline.ingest_clauses(prev_clauses + [fuzzed_clause])

            # Run evaluation
            scope = fuzzed_clause.scope if fuzz_strategy == "narrow_exception" else Scope()
            res = self.pipeline.query(query, as_of_date=as_of, scope=scope)

            # Check outcome
            resolved_correctly = False
            notes = ""
            if fuzz_strategy == "unauthorized_email":
                # Authority check: board policy or T&C must beat email
                if res.winning_clause and res.winning_clause["authority_rank"] > 1:
                    resolved_correctly = True
                    notes = f"Precedence Engine Step 4 eliminated unauthorized email (rank 1); winning rank {res.winning_clause['authority_rank']}."
            elif fuzz_strategy == "future_amendment":
                # In-force check: future amendment must be dropped at Step 2
                if res.winning_clause and res.winning_clause["clause_id"] != fuzzed_clause.clause_id:
                    resolved_correctly = True
                    notes = "Precedence Engine Step 2 dropped future amendment (effective 2026-06-01) for 2025 query date."
            elif fuzz_strategy == "narrow_exception":
                # Specificity check: narrow exception must win for Goa query
                if res.winning_clause and res.winning_clause["clause_id"] == fuzzed_clause.clause_id:
                    resolved_correctly = True
                    notes = "Precedence Engine Step 5 picked narrow regional exception over general rule."
            else:
                # Contradictory FAQ: Board policy must beat FAQ
                if res.winning_clause and res.winning_clause["authority_rank"] > 2:
                    resolved_correctly = True
                    notes = "Precedence Engine Step 4 eliminated FAQ in favor of higher authority policy."

            results.append({
                "fuzz_id": fuzz_id,
                "strategy": fuzz_strategy,
                "injected_clause_id": fuzzed_clause.clause_id,
                "injected_doc": fuzzed_clause.doc_id,
                "topic": topic,
                "query": query,
                "as_of_date": str(as_of),
                "resolved_correctly": resolved_correctly,
                "verdict_status": res.status,
                "winning_clause_id": res.winning_clause["clause_id"] if res.winning_clause else None,
                "notes": notes,
                "new_tickets_count": len(res.new_ledger_tickets)
            })

            # Revert pipeline
            self.pipeline.ingest_clauses(prev_clauses)

        return results
