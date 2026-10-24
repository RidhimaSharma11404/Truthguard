"""
TruthGuard Clause Graph
Maintains clause nodes, relationship edges (amends, withdraws, applies_to),
supersession chain resolution, and graph validation.
"""

from __future__ import annotations
from datetime import date
from typing import Dict, List, Optional, Set, Tuple, Any
from truthguard.schema import Clause, Relation, RelationType


class ClauseGraph:
    def __init__(self):
        self.clauses: Dict[str, Clause] = {}
        # Outgoing edges: source_id -> list of (RelationType, target_id)
        self.outgoing: Dict[str, List[Tuple[RelationType, str]]] = {}
        # Incoming edges: target_id -> list of (RelationType, source_id)
        self.incoming: Dict[str, List[Tuple[RelationType, str]]] = {}

    def add_clause(self, clause: Clause):
        self.clauses[clause.clause_id] = clause
        if clause.clause_id not in self.outgoing:
            self.outgoing[clause.clause_id] = []
        if clause.clause_id not in self.incoming:
            self.incoming[clause.clause_id] = []

        for rel in clause.relations:
            self.outgoing[clause.clause_id].append((rel.type, rel.target))

    def rebuild_edges(self):
        """Re-indexes incoming and outgoing edges for all clauses."""
        self.outgoing = {cid: [] for cid in self.clauses}
        self.incoming = {cid: [] for cid in self.clauses}

        for cid, clause in self.clauses.items():
            for rel in clause.relations:
                self.outgoing[cid].append((rel.type, rel.target))
                if rel.target not in self.incoming:
                    self.incoming[rel.target] = []
                self.incoming[rel.target].append((rel.type, cid))

    def validate_graph(self) -> List[str]:
        """
        Validates relations: ensures every relation target exists in the graph.
        Returns a list of validation error strings.
        """
        errors = []
        for cid, clause in self.clauses.items():
            for rel in clause.relations:
                if rel.target not in self.clauses:
                    errors.append(
                        f"Dangling link in clause {cid}: target '{rel.target}' not found in corpus."
                    )
        return errors

    def get_clause(self, clause_id: str) -> Optional[Clause]:
        return self.clauses.get(clause_id)

    def is_withdrawn(self, clause_id: str, as_of_date: date) -> bool:
        """
        Checks if a clause has been withdrawn by another clause that is active on as_of_date.
        """
        incoming = self.incoming.get(clause_id, [])
        for rel_type, source_id in incoming:
            if rel_type == RelationType.WITHDRAWS:
                withdrawing_clause = self.clauses.get(source_id)
                if withdrawing_clause and withdrawing_clause.is_in_force_on(as_of_date):
                    return True
        return False

    def is_superseded(self, clause_id: str, as_of_date: date) -> Tuple[bool, Optional[str]]:
        """
        Check if clause_id is superseded or withdrawn on as_of_date.
        Follows 'amends' or 'withdraws' links.
        Returns (is_superseded, superseding_clause_id).
        """
        # 1. Check if explicitly withdrawn by an active clause
        if self.is_withdrawn(clause_id, as_of_date):
            for rel_type, source_id in self.incoming.get(clause_id, []):
                if rel_type == RelationType.WITHDRAWS:
                    withdrawer = self.clauses.get(source_id)
                    if withdrawer and withdrawer.is_in_force_on(as_of_date):
                        return True, source_id

        # 2. Check if amended by an active clause
        for rel_type, source_id in self.incoming.get(clause_id, []):
            if rel_type in (RelationType.AMENDS, RelationType.SUPERSEDES):
                amending_clause = self.clauses.get(source_id)
                if amending_clause and amending_clause.is_in_force_on(as_of_date):
                    # Check if the amending clause itself was withdrawn
                    if not self.is_withdrawn(source_id, as_of_date):
                        return True, source_id

        return False, None

    def trace_chain(self, clause_id: str) -> List[Dict[str, Any]]:
        """
        Traces the full amendment and revision history for a clause.
        """
        history = []
        visited = set()
        queue = [clause_id]

        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)
            clause = self.clauses.get(curr_id)
            if clause:
                history.append({
                    "clause_id": clause.clause_id,
                    "doc_id": clause.doc_id,
                    "published_date": str(clause.published_date),
                    "effective_from": str(clause.effective_from),
                    "effective_to": str(clause.effective_to) if clause.effective_to else "open",
                    "text": clause.text,
                    "relations": [r.model_dump() for r in clause.relations]
                })

            # Check outgoing amends
            for rel_type, target_id in self.outgoing.get(curr_id, []):
                if target_id not in visited and target_id in self.clauses:
                    queue.append(target_id)

            # Check incoming amends
            for rel_type, src_id in self.incoming.get(curr_id, []):
                if src_id not in visited and src_id in self.clauses:
                    queue.append(src_id)

        return history

    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Exports graph elements for frontend diagram rendering."""
        elements = []
        for cid, c in self.clauses.items():
            elements.append({
                "data": {
                    "id": cid,
                    "label": f"{cid}\n({c.doc_type})",
                    "doc_id": c.doc_id,
                    "type": c.doc_type,
                    "authority": c.authority_rank,
                    "effective_from": str(c.effective_from)
                }
            })
        for cid, edges in self.outgoing.items():
            for rel_type, target_id in edges:
                if target_id in self.clauses:
                    elements.append({
                        "data": {
                            "source": cid,
                            "target": target_id,
                            "label": rel_type.value if hasattr(rel_type, "value") else str(rel_type)
                        }
                    })
        return elements
