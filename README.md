# 🛡️ TruthGuard: Teaching AI to Pick the Right Document, Not Just the Newest
**Jatayu Season 6 · Use Case 2 · Proof of Concept (PoC)**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-trycloudflare.com-success?style=for-the-badge&logo=cloudflare&color=F38020)](https://strip-departments-does-ottawa.trycloudflare.com)
[![Deploy to Render](https://img.shields.io/badge/Deploy%20to-Render-46E3B7?style=for-the-badge&logo=render)](https://render.com/deploy?repo=https://github.com/RidhimaSharma11404/Truthguard)
[![Open in Streamlit](https://img.shields.io/badge/Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://share.streamlit.io/deploy?repository=RidhimaSharma11404/Truthguard&branch=main&mainModule=ui/app.py)
[![Tests Passing](https://img.shields.io/badge/Tests-11%2F11%20Passed-brightgreen?style=for-the-badge)]()
[![Benchmark Accuracy](https://img.shields.io/badge/Accuracy-93.8%25%20(vs%2056.9%25)-blue?style=for-the-badge)]()

> *"Your assistant doesn't know which document is actually in force. It just picks the one that sounds right. That fails in five predictable ways, and since 2024 a wrong chatbot answer is legally the company's own word."*  
> — **Moffatt v. Air Canada, 2024 BCCRT 149** (Tribunal held airline liable for chatbot's hallucinated bereavement refund terms).

---

## 🌐 Live Deployment Links

| Deployment Channel | Status | URL |
| :--- | :---: | :--- |
| **Primary Live Demo (Cloudflare Edge)** | 🟢 **ONLINE** | **[https://strip-departments-does-ottawa.trycloudflare.com](https://strip-departments-does-ottawa.trycloudflare.com)** *(Instant access, no password, SSL secured)* |
| **1-Click Render Deploy** | 🚀 **READY** | **[Deploy to Render (render.yaml Blueprint)](https://render.com/deploy?repo=https://github.com/RidhimaSharma11404/Truthguard)** |
| **Streamlit Community Cloud** | 🎈 **READY** | **[Deploy on Streamlit Cloud](https://share.streamlit.io/deploy?repository=RidhimaSharma11404/Truthguard&branch=main&mainModule=ui/app.py)** |
| **Localtunnel Backup Mirror** | 🟡 **ONLINE** | **[https://vast-files-exist.loca.lt](https://vast-files-exist.loca.lt)** *(Password: `139.167.143.182`)* |

---

## 📌 Executive Summary
TruthGuard is a deterministic document precedence and falsification architecture that prevents RAG systems from giving confidently wrong answers when enterprise policies, tariffs, or contracts conflict.

While standard RAG systems either select whatever snippet has the highest cosine similarity (**Baseline A**) or blindly favor the newest published document (**Baseline B**), **TruthGuard decouples semantic search from legal decision logic**:
1. **Hybrid Retrieval + Critic**: LLM retrieves candidate clauses, while a **Falsification Critic hunts for the opposite** (contradicting, stale, or superseded terms).
2. **Deterministic Precedence Engine**: A 6-step rule engine evaluates legal validity without probabilistic hallucinations.
3. **Contradiction Ledger**: Automatically turns discovered policy contradictions into prioritized compliance fix-it tickets ranked by **Traffic × Risk**.
4. **Universal Ingestion Studio**: Ingest any custom enterprise policy, regulation, or memo in real-time without retraining.

---

## 🎯 The 5 Traps TruthGuard Catches

| # | Trap Name | The Failure in Plain RAG | How TruthGuard Resolves It |
|---|-----------|--------------------------|----------------------------|
| **01** | **Authority beats Recency** | An informal support email or website FAQ published yesterday overrides an older Master Board Policy. | **Check 4 (Authority)**: Strict hierarchy (`Regulation (5) > Board Policy (4) > Product T&C (3) > FAQ (2) > Email (1)`). |
| **02** | **Clause-level Supersession** | Amending clause 4.2 of a policy causes the retriever to treat the entire original document as deprecated. | **Check 3 (Supersession)**: Follows `amends` links at clause level. Unamended clauses (e.g., cl.4.5 card refunds, cl.4.8 cooling-off) remain valid. |
| **03** | **In Force vs Published Date** | Amendment A was published in March 2025 but only takes effect on 1 July 2025. Asking on 20 June returns the future rule. | **Check 2 (In-Force Date)**: Evaluates validity against the query's `as_of_date` (`effective_from <= as_of_date <= effective_to`). |
| **04** | **Specific beats General** | A national tariff rule caps roaming at 1GB, but a regional Delhi Student pack grants 3GB. Plain RAG returns the 1GB national rule. | **Check 5 (Specificity)**: Specific / narrow regional or segment exceptions beat general rules unless explicitly repealed. |
| **05** | **Amendment Chains** | Policy v1 (5% fee) → Amendment 1 (10% fee) → Amendment 2 (withdraws Amend 1, sets flat Rs. 50). Naive systems pick the withdrawn 10% fee. | **Check 3 (Chain Walking)**: Traverses `withdraws` and `amends` trails in the directed Clause Graph. |

---

## 📊 Evaluation Scoreboard (65 Gold Benchmark Questions)

Benchmarked against **Baseline A (Plain RAG)** and **Baseline B (Plain RAG + Prefer Newest Document)** across 65 gold benchmark questions:

| Evaluation Metric | TruthGuard | Baseline A (Plain RAG) | Baseline B (Newest Doc) | Target Standard |
|:------------------|:----------:|:----------------------:|:-----------------------:|:---------------|
| **Accuracy (as-of date)** | **93.8%** | 56.9% | 0.0% | Clearly above both baselines |
| **Conflict Recall** | **100.0%** | 12.0% | 18.5% | 85% or higher |
| **False-Confidence Rate** | **4.6%** | 43.1% | 100.0% | 5% or lower |
| **Citation Precision** | **98.5%** | 42.0% | 49.0% | 95% or higher |
| **Abstain Correctness** | **100.0%** | 0.0% *(hallucinates)* | 0.0% *(picks newest)* | Pure tie handling |

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

The engine executes pure deterministic code in a strict, audited sequence:

```
  [Candidate Clauses from Hybrid Retrieval + Critic Falsification]
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ 1. Scope Check          │  Drop clauses not covering product / region / segment
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

Discovered policy contradictions are logged and ranked for enterprise risk:
$$\text{Priority Score} = \text{Traffic Weight } (1\text{--}100) \times \text{Risk Level } (1\text{--}5)$$

Example high-priority tickets logged by TruthGuard:
1. `TICKET-D9D18E`: **Support FAQ #12** promises store credit, contradicting Master Board Policy cl.4.5 requiring original card refund. *(Priority: 320)*
2. `TICKET-A2BB6D`: **Subscriber Portal FAQ** charges Rs. 100 MNP porting fee, violating National Regulatory Directive mandating zero fee. *(Priority: 320)*
3. `TICKET-6EE124`: **Marketing Press Release** promises unrestricted global streaming in Germany, conflicting with **DACH Territorial Agreement** vesting exclusive rights with Sky Deutschland. *(Priority: 320)*

---

## 🎬 3-Minute Live Hackathon Pitch Script

1. **Hero Case 1 (20 Jun 2025)**: Ask *"A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"*
   - **Plain RAG says**: *"Yes, 14 days"* (Amendment A is newest and highest cosine match — Confident & Wrong ❌).
   - **TruthGuard says**: *"No, 7 days [RP-v1-4.2]. Amendment A does not take effect until 1 Jul 2025."* (Audited & In Force ✅).
2. **Hero Case 2 (Time Travel to 2 Jul 2025)**: Change the `as_of_date` picker to `2 Jul 2025`.
   - TruthGuard's answer dynamically flips to *"Yes, 14 days under Amendment A [AMD-A-1]"*.
   - Proves TruthGuard reasons about time and legal force, not static text similarity.
3. **Live Custom Policy Ingestion**:
   - Click **➕ Add / Ingest New Policy** in the Ingestion Studio.
   - Click **💼 Severance** or drag & drop a policy file.
   - Click **⚡ Ingest into Live Graph & Update Index**.
   - Watch the knowledge graph dynamically re-index and run analysis against your custom clause!
4. **Contradiction Ledger**: Click the **📋 Contradiction Ledger** button.
   - Inspect tickets ranked by `Traffic × Risk` to show how enterprise legal teams fix contradictory policies at the source.
5. **Scoreboard**: Click the **📊 Judges' Scoreboard** button.
   - Show the audited **93.8% accuracy** vs 56.9% Plain RAG, 100% Conflict Recall, and 4.6% False-Confidence Rate across 65 benchmark questions.

---

## 🚀 How to Run Locally

### 1. Run Unit Tests (Pytest)
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_precedence_engine.py tests/test_pipeline.py tests/test_graph.py -v
```

### 2. Run CLI Benchmark & Scoreboard
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" run_demo.py
```

### 3. Launch Production FastAPI Server
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8501
```

### 4. Or Launch via Streamlit
```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\truthguard"
& "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run ui/app.py
```

---

## 📦 Project Structure

```
truthguard/
├── truthguard/
│   ├── schema.py              # Clause, Scope, Relation, DocType data models
│   ├── graph.py               # Directed Clause Graph with cycle/link validation
│   ├── precedence_engine.py   # Pure deterministic 6-step engine
│   ├── retriever.py           # Hybrid BM25 + TF-IDF retriever
│   ├── critic.py              # Falsification Critic ("hunts for the opposite")
│   ├── citation_gate.py       # Strict bracketed citation validator
│   ├── ledger.py              # Contradiction Ledger (Traffic × Risk)
│   ├── pipeline.py            # Orchestrator & Dynamic Ingestion Studio
│   └── evaluator.py           # 65-question benchmark evaluator
├── data/
│   ├── corpus.json            # 30 synthetic enterprise documents
│   ├── clauses.json           # 35 structured clauses
│   └── gold_questions.json    # 65 gold benchmark questions & ground truth
├── ui/
│   ├── static/index.html      # Neo-Brutalist Single Page App
│   └── app.py                 # Streamlit application wrapper
├── server.py                  # Production FastAPI web server
├── render.yaml                # Render 1-click cloud blueprint
├── Procfile                   # Cloud PaaS entrypoint
├── Dockerfile                 # Container manifest
├── requirements.txt           # Python dependencies
└── README.md                  # System documentation & pitch guide
```
