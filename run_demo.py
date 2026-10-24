"""
TruthGuard CLI Demo & Benchmark Runner
Runs:
1. Hero Case Verification (20 Jun vs 2 Jul)
2. Scoreboard Benchmark vs Baseline A & Baseline B
3. Contradiction Ledger Inspection
4. Conflict Fuzzer Demonstration
"""

import json
from datetime import date
from pathlib import Path
from truthguard.schema import Clause, Scope
from truthguard.pipeline import TruthGuardPipeline
from truthguard.evaluator import BenchmarkEvaluator
from truthguard.fuzzer import ConflictFuzzer


def main():
    print("=" * 80)
    print("  TRUTHGUARD: Teaching AI to pick the right document, not just the newest")
    print("  Jatayu Season 6 · Use Case 2 Proof of Concept")
    print("=" * 80)

    # 1. Load Corpus
    with open("data/clauses.json", "r", encoding="utf-8") as f:
        clauses = [Clause(**c) for c in json.load(f)]
    print(f"\n[+] Ingested {len(clauses)} clauses into TruthGuard Clause Graph and Hybrid Index.")

    pipeline = TruthGuardPipeline()
    pipeline.ingest_clauses(clauses)

    # 2. Hero Case: 20 Jun 2025 vs 2 Jul 2025
    hero_question = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"
    print("\n" + "-" * 80)
    print("HERO DEMO CASE 1: Query as-of 20 Jun 2025")
    print(f"Question: \"{hero_question}\"")
    print("-" * 80)

    cmp_20_jun = pipeline.compare_side_by_side(hero_question, as_of_date=date(2025, 6, 20))
    print(f"  [Baseline A - Plain RAG] : {cmp_20_jun['plain_rag_baseline_a']['answer']}")
    print(f"  [TruthGuard Verdict]     : {cmp_20_jun['truthguard']['status']}")
    print(f"  [TruthGuard Answer]      :\n    {cmp_20_jun['truthguard']['answer'].replace(chr(10), chr(10) + '    ')}")
    print(f"  [Winning Clause]         : {cmp_20_jun['truthguard']['winning_clause']['clause_id']} ({cmp_20_jun['truthguard']['winning_clause']['doc_id']})")

    print("\n" + "-" * 80)
    print("HERO DEMO CASE 2: Same Question, Moving as-of date to 2 Jul 2025")
    print("-" * 80)
    cmp_2_jul = pipeline.compare_side_by_side(hero_question, as_of_date=date(2025, 7, 2))
    print(f"  [Baseline A - Plain RAG] : {cmp_2_jul['plain_rag_baseline_a']['answer']}")
    print(f"  [TruthGuard Verdict]     : {cmp_2_jul['truthguard']['status']}")
    print(f"  [TruthGuard Answer]      :\n    {cmp_2_jul['truthguard']['answer'].replace(chr(10), chr(10) + '    ')}")
    print(f"  [Winning Clause]         : {cmp_2_jul['truthguard']['winning_clause']['clause_id']} ({cmp_2_jul['truthguard']['winning_clause']['doc_id']})")

    # 3. Contradiction Ledger
    print("\n" + "=" * 80)
    print("CONTRADICTION LEDGER (Fix-It Tickets Ranked by Traffic × Risk)")
    print("=" * 80)
    tickets = pipeline.ledger.get_ranked_tickets()
    for t in tickets[:5]:
        print(f"  [{t.ticket_id}] Priority: {t.priority_score} (Traffic={t.traffic_weight} × Risk={t.risk_level}) | Status: {t.status.value}")
        print(f"    Owner: {t.doc_owner} | Category: {t.trap_category}")
        print(f"    Conflict: {t.summary}")
        print(f"    Action:   {t.recommended_action}\n")

    # 4. Scoreboard Evaluation
    print("=" * 80)
    print("EVALUATION SCOREBOARD (65 Gold Benchmark Questions)")
    print("=" * 80)
    evaluator = BenchmarkEvaluator(pipeline)
    scoreboard = evaluator.run_benchmark()

    print(f"\n{'Metric':<25} | {'TruthGuard':<12} | {'Baseline A':<12} | {'Baseline B':<12} | {'Target':<20}")
    print("-" * 90)
    for m in scoreboard["metrics"]:
        print(f"{m['metric']:<25} | {m['truthguard']:<12} | {m['baseline_a']:<12} | {m['baseline_b']:<12} | {m['proposed_target']:<20}")

    print("\nPer-Trap Accuracy Breakdown:")
    print(f"{'Trap Name':<28} | {'Total':<6} | {'TruthGuard':<12} | {'Baseline A':<12} | {'Baseline B':<12}")
    print("-" * 75)
    for trap, stats in scoreboard["per_trap_breakdown"].items():
        print(f"{trap:<28} | {stats['total']:<6} | {stats['truthguard_acc']:<12} | {stats['baseline_a_acc']:<12} | {stats['baseline_b_acc']:<12}")

    # 5. Conflict Fuzzer
    print("\n" + "=" * 80)
    print("CONFLICT FUZZER DEMO (Injecting 3 Real-time Conflicting Clauses)")
    print("=" * 80)
    fuzzer = ConflictFuzzer(pipeline)
    fuzz_results = fuzzer.run_fuzz_cycle(num_injections=3)
    for fr in fuzz_results:
        status_icon = "[PASS]" if fr["resolved_correctly"] else "[FAIL]"
        print(f"  {status_icon} [{fr['fuzz_id']}] Strategy: {fr['strategy']} | Injected: {fr['injected_clause_id']}")
        print(f"    Notes: {fr['notes']}")


if __name__ == "__main__":
    main()
