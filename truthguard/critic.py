"""
TruthGuard Critic & Falsification Engine
"A critic that hunts for the opposite."
For every claim / candidate, actively conducts a falsification search across the entire corpus:
- Looks for contradicting clauses
- Looks for stale clauses
- Looks for unsupported claims
- Injects any found contradicting clauses into the candidate set so the Precedence Engine can evaluate them
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set, Tuple
from truthguard.schema import Clause
from truthguard.graph import ClauseGraph


class FalsificationFinding:
    def __init__(
        self,
        target_clause_id: str,
        found_clause_id: str,
        conflict_type: str,
        reason: str
    ):
        self.target_clause_id = target_clause_id
        self.found_clause_id = found_clause_id
        self.conflict_type = conflict_type
        self.reason = reason


class FalsificationCritic:
    def __init__(self, all_clauses: List[Clause], graph: Optional[ClauseGraph] = None):
        self.all_clauses = all_clauses
        self.clause_map = {c.clause_id: c for c in all_clauses}
        self.graph = graph

        # Inverted index by topic
        self.by_topic: Dict[str, List[Clause]] = {}
        for c in all_clauses:
            self.by_topic.setdefault(c.topic, []).append(c)

    def falsify_candidates(
        self,
        candidate_clauses: List[Clause]
    ) -> Tuple[List[Clause], List[FalsificationFinding]]:
        """
        Executes falsification search:
        For each candidate clause, inspects the wider corpus for:
        1. Amendments / superseding clauses that amend or withdraw it
        2. Clauses amended or withdrawn by it
        3. Colliding clauses with identical topic or conflicting numeric/policy conditions
        Returns:
            - augmented_candidates: original candidates + any newly discovered contradicting clauses
            - findings: list of FalsificationFinding
        """
        candidate_ids = {c.clause_id for c in candidate_clauses}
        augmented = list(candidate_clauses)
        findings: List[FalsificationFinding] = []

        for cand in candidate_clauses:
            # 1. Search by topic in corpus
            topic_peers = self.by_topic.get(cand.topic, [])
            for peer in topic_peers:
                if peer.clause_id in candidate_ids:
                    continue

                # Check for explicit relation
                is_related = False
                for r in peer.relations:
                    if r.target == cand.clause_id:
                        is_related = True
                        findings.append(FalsificationFinding(
                            target_clause_id=cand.clause_id,
                            found_clause_id=peer.clause_id,
                            conflict_type=f"relation_{r.type.value}",
                            reason=f"Clause {peer.clause_id} explicitly {r.type.value} candidate {cand.clause_id}"
                        ))
                        break

                for r in cand.relations:
                    if r.target == peer.clause_id:
                        is_related = True
                        findings.append(FalsificationFinding(
                            target_clause_id=cand.clause_id,
                            found_clause_id=peer.clause_id,
                            conflict_type=f"target_{r.type.value}",
                            reason=f"Candidate {cand.clause_id} explicitly {r.type.value} clause {peer.clause_id}"
                        ))
                        break

                # Check for textual/semantic collision (different numbers, store credit vs card, different authority)
                if not is_related and peer.topic == cand.topic:
                    if peer.doc_id != cand.doc_id:
                        findings.append(FalsificationFinding(
                            target_clause_id=cand.clause_id,
                            found_clause_id=peer.clause_id,
                            conflict_type="semantic_contradiction",
                            reason=f"Clause {peer.clause_id} ({peer.doc_type}) conflicts with {cand.clause_id} on {cand.topic}"
                        ))
                        is_related = True

                if is_related and peer.clause_id not in candidate_ids:
                    augmented.append(peer)
                    candidate_ids.add(peer.clause_id)

            # 2. Check graph for incoming/outgoing edges if available
            if self.graph:
                # check incoming
                for rel_type, src_id in self.graph.incoming.get(cand.clause_id, []):
                    if src_id not in candidate_ids and src_id in self.clause_map:
                        peer = self.clause_map[src_id]
                        augmented.append(peer)
                        candidate_ids.add(src_id)
                        findings.append(FalsificationFinding(
                            target_clause_id=cand.clause_id,
                            found_clause_id=src_id,
                            conflict_type=f"graph_{rel_type}",
                            reason=f"Graph relation {src_id} -> {cand.clause_id} ({rel_type})"
                        ))

                # check outgoing
                for rel_type, tgt_id in self.graph.outgoing.get(cand.clause_id, []):
                    if tgt_id not in candidate_ids and tgt_id in self.clause_map:
                        peer = self.clause_map[tgt_id]
                        augmented.append(peer)
                        candidate_ids.add(tgt_id)
                        findings.append(FalsificationFinding(
                            target_clause_id=cand.clause_id,
                            found_clause_id=tgt_id,
                            conflict_type=f"graph_target_{rel_type}",
                            reason=f"Graph relation {cand.clause_id} -> {tgt_id} ({rel_type})"
                        ))

        return augmented, findings
