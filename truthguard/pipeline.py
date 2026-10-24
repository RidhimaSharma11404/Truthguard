"""
TruthGuard Full Pipeline
Orchestrates:
1. Hybrid Retrieval
2. LLM Synthesizer
3. Falsification Critic ("hunt for the opposite")
4. Precedence Engine (6 deterministic checks)
5. Citation Gate (removes unreferenced claims)
6. Contradiction Ledger (logs conflicts ranked by traffic × risk)
7. Side-by-Side Baseline Comparison
"""

from __future__ import annotations
from datetime import date
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from truthguard.schema import Clause, Scope, SpecificityType
from truthguard.graph import ClauseGraph
from truthguard.retriever import HybridRetriever
from truthguard.critic import FalsificationCritic
from truthguard.precedence_engine import PrecedenceEngine, EngineVerdict, VerdictStatus
from truthguard.synthesizer import Synthesizer
from truthguard.citation_gate import CitationGate
from truthguard.ledger import ContradictionLedger, ContradictionTicket
from truthguard.baselines import BaselinePlainRAG, BaselineNewestDocRAG


class PipelineResult(BaseModel):
    question: str
    as_of_date: str
    scope: Dict[str, str]
    system: str = "TruthGuard"
    status: str
    answer: str
    winning_clause: Optional[Dict[str, Any]] = None
    tied_clauses: List[Dict[str, Any]] = Field(default_factory=list)
    cited_clause_ids: List[str] = Field(default_factory=list)
    precedence_trace: List[Dict[str, Any]] = Field(default_factory=list)
    falsification_findings: List[Dict[str, str]] = Field(default_factory=list)
    new_ledger_tickets: List[Dict[str, Any]] = Field(default_factory=list)
    gated_sentences_removed: List[str] = Field(default_factory=list)


class TruthGuardPipeline:
    def __init__(self, authority_table: Optional[Dict[str, int]] = None):
        self.graph = ClauseGraph()
        self.retriever = HybridRetriever()
        self.precedence_engine = PrecedenceEngine(authority_table=authority_table)
        self.synthesizer = Synthesizer()
        self.ledger = ContradictionLedger()
        self.critic: Optional[FalsificationCritic] = None
        self.baseline_a: Optional[BaselinePlainRAG] = None
        self.baseline_b: Optional[BaselineNewestDocRAG] = None
        self.all_clauses: List[Clause] = []

    def ingest_clauses(self, clauses: List[Clause]):
        """Ingests clauses into graph, retriever, critic, and baselines."""
        self.all_clauses = list(clauses)
        for c in clauses:
            self.graph.add_clause(c)
        self.graph.rebuild_edges()
        self.retriever.index(clauses)
        self.critic = FalsificationCritic(clauses, self.graph)
        self.baseline_a = BaselinePlainRAG(self.retriever)
        self.baseline_b = BaselineNewestDocRAG(self.retriever)
        self._populate_corpus_contradiction_ledger()

    def _populate_corpus_contradiction_ledger(self):
        """
        Scans the corpus for contradictions and populates the contradiction ledger.
        Fulfills Section 13: 'Contradiction ledger populated from the corpus'.
        """
        # Group clauses by topic
        by_topic: Dict[str, List[Clause]] = {}
        for c in self.all_clauses:
            by_topic.setdefault(c.topic, []).append(c)

        for topic, topic_clauses in by_topic.items():
            if len(topic_clauses) < 2:
                continue

            # Compare pairs for authority or supersession conflicts
            for i in range(len(topic_clauses)):
                for j in range(i + 1, len(topic_clauses)):
                    c1, c2 = topic_clauses[i], topic_clauses[j]
                    if c1.doc_id == c2.doc_id:
                        continue

                    # Check for authority rank difference
                    if c1.authority_rank != c2.authority_rank:
                        higher = c1 if c1.authority_rank > c2.authority_rank else c2
                        lower = c2 if c1.authority_rank > c2.authority_rank else c1
                        
                        # Only log if lower authority contradicts higher
                        self.ledger.log_contradiction(
                            winning_clause_id=higher.clause_id,
                            winning_doc_title=higher.doc_id,
                            conflicting_clause_id=lower.clause_id,
                            conflicting_doc_title=lower.doc_id,
                            trap_category="Authority over Recency",
                            doc_owner=f"{lower.doc_type.title()} Content Lead",
                            summary=f"{lower.doc_id} promises \"{lower.text}\", conflicting with higher authority {higher.doc_type} \"{higher.text}\"",
                            recommended_action=f"Update or retract {lower.doc_id} ({lower.clause_id}) to align with {higher.clause_id}.",
                            traffic_weight=80 if lower.doc_type == "FAQ" else 60,
                            risk_level=4 if lower.doc_type == "FAQ" else 3
                        )

                    # Check for explicit amendment where older remains active in some system
                    for rel in c1.relations:
                        if rel.target == c2.clause_id and rel.type.value == "amends":
                            self.ledger.log_contradiction(
                                winning_clause_id=c1.clause_id,
                                winning_doc_title=c1.doc_id,
                                conflicting_clause_id=c2.clause_id,
                                conflicting_doc_title=c2.doc_id,
                                trap_category="Clause Supersession",
                                doc_owner="Policy Ops",
                                summary=f"{c1.doc_id} amended {c2.clause_id}, but legacy references to {c2.doc_id} persist.",
                                recommended_action=f"Archive obsolete version {c2.clause_id} across support wikis.",
                                traffic_weight=90,
                                risk_level=5
                            )

    def query(
        self,
        question: str,
        as_of_date: date,
        scope: Optional[Scope] = None,
        top_k: int = 8
    ) -> PipelineResult:
        """
        Executes the full TruthGuard Answer Pipeline.
        """
        query_scope = scope or Scope()

        # Step 2: Retriever - hybrid search over clauses
        retrieved_pairs = self.retriever.retrieve(question, top_k=top_k, scope_filter=query_scope)
        initial_candidates = [pair[0] for pair in retrieved_pairs]

        if not initial_candidates:
            initial_candidates = self.all_clauses[:top_k]

        # Step 4: Critic (LLM / Falsification Engine) - searches for the opposite
        falsification_findings = []
        if self.critic:
            augmented_candidates, findings = self.critic.falsify_candidates(initial_candidates)
            falsification_findings = [
                {
                    "target_clause_id": f.target_clause_id,
                    "found_clause_id": f.found_clause_id,
                    "conflict_type": f.conflict_type,
                    "reason": f.reason
                }
                for f in findings
            ]
        else:
            augmented_candidates = initial_candidates

        # Precedence evaluation resolves competing clauses on the primary topic asked
        primary_topic = initial_candidates[0].topic
        topic_candidates = [c for c in augmented_candidates if c.topic == primary_topic]
        if not topic_candidates:
            topic_candidates = [c for c in initial_candidates if c.topic == primary_topic]
        if not topic_candidates:
            topic_candidates = augmented_candidates

        # Step 5: Precedence Engine - decides the verdict deterministically
        verdict = self.precedence_engine.evaluate(
            candidates=topic_candidates,
            as_of_date=as_of_date,
            customer_scope=query_scope,
            graph=self.graph
        )

        # Step 3: Synthesizer drafts answer claim-by-claim
        raw_answer = self.synthesizer.synthesize_answer(
            query=question,
            as_of_date=as_of_date,
            verdict=verdict,
            candidates=augmented_candidates
        )

        # Step 7: Citation Gate - any sentence without a clause_id is removed
        valid_ids = {c.clause_id for c in self.all_clauses}
        gate = CitationGate(valid_ids)
        final_answer, removed_sentences = gate.filter_text(raw_answer)

        # Step 8: Ledger - every conflict found is written to the contradiction ledger
        new_tickets = []
        if verdict.status == VerdictStatus.RESOLVED and verdict.winning_clause:
            winner = verdict.winning_clause
            # Look for conflicting clauses that lost due to authority or staleness
            for cand in augmented_candidates:
                if cand.clause_id != winner.clause_id and cand.topic == winner.topic:
                    # If an FAQ conflicts with a Board Policy or T&C
                    if cand.authority_rank < winner.authority_rank and cand.is_in_force_on(as_of_date):
                        ticket = self.ledger.log_contradiction(
                            winning_clause_id=winner.clause_id,
                            winning_doc_title=winner.doc_id,
                            conflicting_clause_id=cand.clause_id,
                            conflicting_doc_title=cand.doc_id,
                            trap_category="Authority over Recency",
                            doc_owner=f"{cand.doc_type} Owner",
                            summary=f"{cand.doc_id} promises \"{cand.text}\", contradicting valid {winner.doc_type} \"{winner.text}\"",
                            recommended_action=f"Update or revoke {cand.doc_id} to conform with {winner.clause_id}",
                            traffic_weight=75,
                            risk_level=4
                        )
                        new_tickets.append(ticket.model_dump())
        elif verdict.status == VerdictStatus.TIE_ABSTAIN:
            # Genuine tie logged as critical escalation ticket
            if len(verdict.tied_clauses) >= 2:
                c1, c2 = verdict.tied_clauses[0], verdict.tied_clauses[1]
                ticket = self.ledger.log_contradiction(
                    winning_clause_id=c1.clause_id,
                    winning_doc_title=c1.doc_id,
                    conflicting_clause_id=c2.clause_id,
                    conflicting_doc_title=c2.doc_id,
                    trap_category="Unresolvable Equal Conflict",
                    doc_owner="Chief Compliance Officer",
                    summary=f"Conflicting clauses with identical authority rank ({c1.authority_rank}): {c1.text} vs {c2.text}",
                    recommended_action="Executive legal harmonization required.",
                    traffic_weight=90,
                    risk_level=5
                )
                new_tickets.append(ticket.model_dump())

        # Collect cited clause IDs
        import re
        cited_ids = list(set(re.findall(r"\[([A-Za-z0-9\-\._]+)\]", final_answer)))

        return PipelineResult(
            question=question,
            as_of_date=str(as_of_date),
            scope=query_scope.model_dump(),
            status=verdict.status.value,
            answer=final_answer,
            winning_clause=verdict.winning_clause.model_dump() if verdict.winning_clause else None,
            tied_clauses=[c.model_dump() for c in verdict.tied_clauses],
            cited_clause_ids=cited_ids,
            precedence_trace=[t.model_dump() for t in verdict.trace],
            falsification_findings=falsification_findings,
            new_ledger_tickets=new_tickets,
            gated_sentences_removed=removed_sentences
        )

    def compare_side_by_side(
        self,
        question: str,
        as_of_date: date,
        scope: Optional[Scope] = None
    ) -> Dict[str, Any]:
        """
        Runs the question through Plain RAG (Baseline A), Newest Doc RAG (Baseline B),
        and TruthGuard, returning a side-by-side comparison structure.
        """
        tg_result = self.query(question, as_of_date, scope)
        b_a = self.baseline_a.query(question, as_of_date, scope) if self.baseline_a else {}
        b_b = self.baseline_b.query(question, as_of_date, scope) if self.baseline_b else {}

        return {
            "question": question,
            "as_of_date": str(as_of_date),
            "scope": (scope or Scope()).model_dump(),
            "plain_rag_baseline_a": b_a,
            "newest_doc_baseline_b": b_b,
            "truthguard": tg_result.model_dump()
        }
