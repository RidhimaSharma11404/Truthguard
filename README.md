# 🛡️ TruthGuard: Teaching AI to Pick the Right Document, Not Just the Newest
**Jatayu Season 6 · Use Case 2 · Proof of Concept (PoC)**

> *"Your assistant doesn't know which document is actually in force. It just picks the one that sounds right. That fails in five predictable ways, and since 2024 a wrong chatbot answer is legally the company's own word."*
> — **Moffatt v. Air Canada, 2024 BCCRT 149**

---

## 📌 Executive Summary
TruthGuard is a deterministic document precedence and falsification architecture that prevents RAG systems from giving confidently wrong answers when enterprise policies, tariffs, or contracts conflict.

While naive RAG systems either select whatever snippet has the highest cosine similarity (Baseline A) or blindly favor the newest published document (Baseline B), **TruthGuard decouples text understanding from decision logic**:
- **LLMs read and propose claims** with citations.
- **A Critic hunts for the opposite** (falsification search for contradicting, stale, or superseded terms).
- A **Deterministic Precedence Engine (6 strict checks)** disposes and decides the winning clause.
- A **Contradiction Ledger** automatically turns discovered policy conflicts into fix-it tickets ranked by **Traffic × Risk**.

---

## 🎯 The 5 Traps TruthGuard Catches

| # | Trap Name | The Failure in Plain RAG | How TruthGuard Resolves It |
|---|-----------|--------------------------|----------------------------|
| **01** | **Authority beats Recency** | An informal support email or website FAQ published yesterday overrides an older Master Board Policy. | **Check 4 (Authority)**: Strict hierarchy (`Regulation (5) > Board Policy (4) > Product T&C (3) > FAQ (2) > Email (1)`). |
| **02** | **Clause-level Supersession** | Amending clause 4.2 of a policy causes the retriever to treat the entire original document as deprecated. | **Check 3 (Supersession)**: Follows `amends` links at the clause level. Unamended clauses (e.g., cl.4.5 card refunds, cl.4.8 cooling-off) remain valid. |
| **03** | **In Force vs Published Date** | Amendment A was published in March 2025 but only takes effect on 1 July 2025. Asking on 20 June returns the future rule. | **Check 2 (In-Force Date)**: Evaluates validity against the query's `as_of_date` (`effective_from <= as_of_date <= effective_to`). |
| **04** | **Specific beats General** | A national tariff rule caps roaming at 1GB, but a regional Delhi Student pack grants 3GB. A plain RAG retriever returns the 1GB national rule. | **Check 5 (Specificity)**: Specific / narrow regional or segment exceptions beat general rules unless explicitly repealed. |
| **05** | **Amendment Chains** | Policy v1 (5% late fee) → Amendment 1 (10% fee) → Amendment 2 (withdraws Amendment 1, sets flat Rs. 50). Naive systems pick the withdrawn 10% fee. | **Check 3 (Chain Walking)**: Traverses `withdraws` and `amends` trails in the Clause Graph. |

---

## 📊 Evaluation Scoreboard (65 Gold Benchmark Questions)

Benchmarked against **Baseline A (Plain RAG)** and **Baseline B (Plain RAG + Prefer Newest Document)** across 65 gold benchmark questions:

| Metric | TruthGuard | Baseline A (Plain RAG) | Baseline B (Newest Doc) | Target |
|:-------|:----------:|:----------------------:|:-----------------------:|:-------|
| **Accuracy (as-of date)** | **93.8%** | 56.9% | 0.0% | Clearly above both baselines |
| **Conflict Recall** | **100.0%** | 12.0% | 18.5% | 85% or higher |
| **False-Confidence Rate** | **4.6%** | 43.1% | 100.0% | 5% or lower |
| **Citation Precision** | **98.5%** | 42.0% | 49.0% | 95% or higher |
| **Abstain Correctness** | **100.0%** | 0.0% *(hallucinates)* | 0.0% *(picks newest)* | Report as is |

### Per-Trap Accuracy Breakdown
- **Trap 1: Authority over Recency**: `100.0%`
- **Trap 2: Clause-level Supersession**: `90.0%`
- **Trap 3: In-Force vs Published Date**: `100.0%`
- **Trap 4: Specific over General**: `91.7%`
- **Trap 5: Amendment Chains**: `90.9%`
- **Control Questions**: `88.9%`
- **Unresolvable Conflict (Abstain Correctness)**: `100.0%`

---

## ⚙️ The Precedence Engine: 6 Deterministic Checks
The engine executes pure code without LLM calls in a fixed sequence:
```
  [Candidate Clauses from Hybrid Retrieval + Critic Falsification]
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ 1. Scope Check          │  Drop clauses not covering product/region/segment
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 2. In-Force Date Check  │  Drop clauses not effective on query as_of_date
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 3. Supersession Trail   │  Follow amends/withdraws; drop replaced clauses
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 4. Authority Hierarchy  │  Keep highest rank: Regulation > Board > T&C > FAQ > Email
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 5. Specificity Check    │  Narrow regional/segment exception beats general rule
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 6. Recency Tie-Breaker  │  Newer wins only between otherwise equal clauses
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              Single Winner              Tied Clauses
          [Answer with Citations]    [System Abstains & Logs Ticket]
```

---

## 📋 Contradiction Ledger (Fix-It Tickets)
Discovered conflicts between active policies and stale/unauthorized documents are prioritized by:
$$\text{Priority Score} = \text{Traffic Weight (1–100)} \times \text{Risk Level (1–5)}$$

Example high-priority tickets logged by the system:
1. `TICKET-D9D18E`: **Support FAQ #12** promises store credit, contradicting Master Board Policy **cl.4.5** requiring original card refund. *(Priority: 320)*
2. `TICKET-A2BB6D`: **Subscriber Portal FAQ** charges Rs. 100 MNP porting fee, violating National **Regulatory Directive** mandating zero fee. *(Priority: 320)*
3. `TICKET-6EE124`: **Marketing Press Release** promises unrestricted global streaming in Germany, conflicting with **DACH Territorial Agreement** vesting exclusive rights with Sky Deutschland. *(Priority: 320)*

---

## 🚀 How to Run

### 1. Run Unit Tests (Pytest)
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_precedence_engine.py tests/test_pipeline.py tests/test_graph.py -v
```

### 2. Run the Full Demo & Scoreboard Benchmark CLI
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" run_demo.py
```

### 3. Launch the Interactive Web Dashboard (Streamlit)
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run ui/app.py
```

---

## 🎬 3-Minute Demo Script (For Hackathon Pitch)
1. **Hero Case 1 (20 Jun 2025)**: Ask *"A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"*
   - Plain RAG says: *"Yes, 14 days"* (Amendment A is newest and best match).
   - TruthGuard says: *"No, 7 days [RP-v1-4.2]. Amendment A does not take effect until 1 Jul 2025."*
2. **Hero Case 2 (Time Travel to 2 Jul 2025)**: Change the `as_of_date` picker to `2 Jul 2025`.
   - TruthGuard's answer flips to *"Yes, 14 days under Amendment A [AMD-A-1]"*.
   - Proves TruthGuard reasons about time and legal force, not text similarity.
3. **Contradiction Ledger**: Switch to the **Contradiction Ledger** tab.
   - Show `FAQ #12` flagged with Priority 320 for promising store credit against Board Policy cl.4.5.
4. **Scoreboard**: Switch to the **Evaluation Scoreboard** tab.
   - Show the 93.8% accuracy vs 56.9% Plain RAG, 100% Conflict Recall, and 4.6% False-Confidence Rate.
5. **Abstain Case**: Load the Interconnect Carrier SLA question.
   - Shows TruthGuard abstaining and presenting both sources when equal-authority contracts conflict, refusing to hallucinate.
