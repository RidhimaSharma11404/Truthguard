"""
TruthGuard Evaluation Baselines
Implements Baseline A (Plain RAG) and Baseline B (Plain RAG + Prefer Newest Document).
Used for side-by-side comparison and the Scoreboard.
"""

from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple
from truthguard.schema import Clause, Scope
from truthguard.retriever import HybridRetriever


class BaselinePlainRAG:
    """
    Baseline A: Plain RAG
    Simply takes the top-ranked passage from the retriever by text similarity,
    without date checks, authority hierarchy, or supersession.
    Answers confidently and naively.
    """
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def query(self, question: str, as_of_date: date, scope: Optional[Scope] = None) -> dict:
        candidates = self.retriever.retrieve(question, top_k=5)
        if not candidates:
            return {
                "answer": "No relevant document found in knowledge base.",
                "selected_clause": None,
                "confidence": "Low",
                "is_confident": False,
                "system": "Baseline A (Plain RAG)"
            }

        top_clause, score = candidates[0]

        # Naive synthesis: assumes top match is absolute truth
        answer = f"Yes. According to {top_clause.doc_id}: \"{top_clause.text}\""

        return {
            "answer": answer,
            "selected_clause": top_clause,
            "confidence": "High",
            "is_confident": True,
            "system": "Baseline A (Plain RAG)"
        }


class BaselineNewestDocRAG:
    """
    Baseline B: Plain RAG with "Prefer Newest Document" rule
    The strongest naive baseline: sorts candidate passages by published_date descending.
    Fails on Authority vs Recency, In-Force vs Published, Specific vs General, and Amendment Chains.
    """
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def query(self, question: str, as_of_date: date, scope: Optional[Scope] = None) -> dict:
        candidates = self.retriever.retrieve(question, top_k=8)
        if not candidates:
            return {
                "answer": "No relevant document found in knowledge base.",
                "selected_clause": None,
                "confidence": "Low",
                "is_confident": False,
                "system": "Baseline B (Newest Document RAG)"
            }

        # Filter loosely by positive score, then pick newest published_date
        clauses = [c for c, s in candidates]
        newest_clause = max(clauses, key=lambda c: c.published_date)

        answer = f"According to the latest published document ({newest_clause.doc_id}, released {newest_clause.published_date}): \"{newest_clause.text}\""

        return {
            "answer": answer,
            "selected_clause": newest_clause,
            "confidence": "High",
            "is_confident": True,
            "system": "Baseline B (Newest Document RAG)"
        }
