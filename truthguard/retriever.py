"""
TruthGuard Hybrid Retriever (Pure Python)
Lightweight, lightning-fast hybrid search combining BM25 keyword scoring and TF-IDF vector similarity.
Zero external heavy dependencies (no sklearn/scipy loading overhead).
"""

from __future__ import annotations
import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Set
from truthguard.schema import Clause, Scope


def tokenize(text: str) -> List[str]:
    """Extract lowercased alphanumeric tokens of length >= 2, splitting on hyphens and punctuation."""
    # Replace hyphens and dots with spaces so 'cooling-off' -> 'cooling', 'off'
    cleaned = re.sub(r"[\-\./_]", " ", text)
    return re.findall(r"\b[a-zA-Z0-9]{2,}\b", cleaned.lower())


def get_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Generates word unigrams and bigrams."""
    ngrams = list(tokens)
    for i in range(len(tokens) - n + 1):
        ngrams.append("_".join(tokens[i:i+n]))
    return ngrams


class HybridRetriever:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.clauses: List[Clause] = []
        self.clause_map: Dict[str, Clause] = {}
        self.corpus_ngrams: List[List[str]] = []
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.tfidf_vectors: List[Dict[str, float]] = []
        self.vector_norms: List[float] = []
        self.avg_doc_len: float = 0.0

    def index(self, clauses: List[Clause]):
        self.clauses = list(clauses)
        self.clause_map = {c.clause_id: c for c in clauses}
        self.corpus_ngrams = []
        self.doc_freqs = defaultdict(int)
        self.tfidf_vectors = []
        self.vector_norms = []

        if not clauses:
            return

        total_tokens = 0
        for c in clauses:
            doc_str = f"{c.doc_id} {c.doc_type} {c.topic} {c.scope.product} {c.scope.region} {c.text}"
            tokens = tokenize(doc_str)
            ngrams = get_ngrams(tokens, n=2)
            self.corpus_ngrams.append(ngrams)
            total_tokens += len(ngrams)
            for term in set(ngrams):
                self.doc_freqs[term] += 1

        n_docs = len(clauses)
        self.avg_doc_len = total_tokens / max(1, n_docs)

        # Build TF-IDF vectors
        for ngrams in self.corpus_ngrams:
            counts = Counter(ngrams)
            doc_len = len(ngrams)
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for term, count in counts.items():
                df = self.doc_freqs[term]
                idf = math.log((n_docs + 1.0) / (df + 1.0)) + 1.0
                tf = 1.0 + math.log(count) if count > 0 else 0.0
                tfidf = tf * idf
                vec[term] = tfidf
                norm_sq += tfidf * tfidf

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self.tfidf_vectors.append(vec)
            self.vector_norms.append(norm)

    def _bm25_score(self, query_terms: List[str], doc_idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        doc_ngrams = self.corpus_ngrams[doc_idx]
        doc_len = len(doc_ngrams)
        n_docs = len(self.clauses)
        score = 0.0

        counts = Counter(doc_ngrams)
        for term in query_terms:
            if term not in self.doc_freqs:
                continue
            df = self.doc_freqs[term]
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf = counts.get(term, 0)
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
            score += idf * (numerator / max(1e-6, denominator))

        return score

    def _cosine_sim(self, query_terms: List[str], doc_idx: int) -> float:
        n_docs = len(self.clauses)
        q_counts = Counter(query_terms)
        q_vec = {}
        q_norm_sq = 0.0

        for term, count in q_counts.items():
            df = self.doc_freqs.get(term, 0)
            idf = math.log((n_docs + 1.0) / (df + 1.0)) + 1.0
            tf = 1.0 + math.log(count) if count > 0 else 0.0
            val = tf * idf
            q_vec[term] = val
            q_norm_sq += val * val

        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0
        doc_vec = self.tfidf_vectors[doc_idx]
        doc_norm = self.vector_norms[doc_idx]

        dot = 0.0
        for term, q_val in q_vec.items():
            if term in doc_vec:
                dot += q_val * doc_vec[term]

        return dot / (q_norm * doc_norm) if (q_norm * doc_norm) > 0 else 0.0

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        scope_filter: Optional[Scope] = None
    ) -> List[Tuple[Clause, float]]:
        if not self.clauses:
            return []

        tokens = tokenize(query)
        q_ngrams = get_ngrams(tokens, n=2)

        scored = []
        for idx, clause in enumerate(self.clauses):
            v_score = self._cosine_sim(q_ngrams, idx)
            bm_score = self._bm25_score(q_ngrams, idx)
            norm_bm = bm_score / (10.0 + bm_score) if bm_score > 0 else 0.0
            combined = (self.alpha * v_score) + ((1.0 - self.alpha) * norm_bm)

            # Bonus for exact topic keywords
            for tok in tokens:
                if tok in clause.topic.lower():
                    combined += 0.20

            scored.append((clause, combined))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
