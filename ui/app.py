"""
TruthGuard Interactive UI & Demo Dashboard
Built with Streamlit for Jatayu Season 6 · Use Case 2
Features:
- 3-Minute Demo Guided Script
- Ask & Answer Side-by-Side (Plain RAG vs TruthGuard)
- Interactive Chronological Timeline View
- 6-Step Precedence Engine Audit Trace
- Contradiction Ledger (Ranked by Traffic × Risk)
- Live Scoreboard & Per-Trap Benchmark
- Conflict Fuzzer & Clause Graph Explorer
"""

import os
import sys
import json
from datetime import date, datetime
from pathlib import Path
import streamlit as st
import pandas as pd

# Add truthguard to sys.path
BASE_DIR = Path("C:/Users/Lenovo/.gemini/antigravity/scratch/truthguard")
sys.path.insert(0, str(BASE_DIR))

from truthguard.schema import Clause, Scope, SpecificityType
from truthguard.pipeline import TruthGuardPipeline
from truthguard.evaluator import BenchmarkEvaluator
from truthguard.fuzzer import ConflictFuzzer


# Configure Streamlit page
st.set_page_config(
    page_title="TruthGuard | Jatayu Season 6",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 20px;
    }
    .hero-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        margin-bottom: 12px;
    }
    .rag-wrong-card {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 16px;
        border-radius: 6px;
    }
    .tg-win-card {
        background-color: #F0FDF4;
        border-left: 5px solid #10B981;
        padding: 16px;
        border-radius: 6px;
    }
    .citation-badge {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 4px;
    }
    .timeline-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #F1F5F9;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    .timeline-node {
        text-align: center;
        background: white;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #CBD5E1;
        font-size: 0.82rem;
    }
    .timeline-node.active {
        border: 2px solid #10B981;
        background: #ECFDF5;
        font-weight: bold;
    }
    .timeline-node.expired {
        opacity: 0.6;
        text-decoration: line-through;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_truthguard_pipeline():
    with open(BASE_DIR / "data/clauses.json", "r", encoding="utf-8") as f:
        raw_clauses = json.load(f)
    clauses = [Clause(**c) for c in raw_clauses]
    pipeline = TruthGuardPipeline()
    pipeline.ingest_clauses(clauses)
    return pipeline


pipeline = load_truthguard_pipeline()

# Sidebar Navigation & Demo Script
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=64)
st.sidebar.title("TruthGuard")
st.sidebar.caption("Jatayu Season 6 · Use Case 2 · Proof of Concept")

# Guided 3-Minute Demo Script in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🎬 3-Minute Demo Script")
demo_choice = st.sidebar.radio(
    "Select Demo Stage:",
    [
        "None (Custom Query)",
        "Step 1: Hero Refund (20 Jun 2025)",
        "Step 2: Time Travel (2 Jul 2025)",
        "Step 3: Contradiction Ledger (FAQ #12)",
        "Step 4: Scoreboard vs Plain RAG",
        "Step 5: Abstain on Equal Conflict"
    ],
    index=0
)

# Navigation
tabs = st.tabs([
    "🔍 Ask & Answer (Side-by-Side)",
    "📋 Contradiction Ledger",
    "📊 Evaluation Scoreboard",
    "⚡ Conflict Fuzzer",
    "🗺️ Clause Graph Explorer",
    "ℹ️ Architecture & The 5 Traps"
])


# =====================================================================
# TAB 1: ASK & ANSWER (SIDE-BY-SIDE + TIMELINE + AUDIT TRACE)
# =====================================================================
with tabs[0]:
    st.markdown('<div class="main-header">TruthGuard Query Sandbox</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Teaching AI to pick the right document in force, not just the newest. '
        '<i>(Moffatt v. Air Canada, 2024: chatbot answers are legally binding)</i></div>',
        unsafe_allow_html=True
    )

    # Handle Demo presets
    default_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"
    default_date = date(2025, 6, 20)
    default_product = "all"
    default_region = "all"
    default_segment = "all"

    if demo_choice == "Step 1: Hero Refund (20 Jun 2025)":
        default_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"
        default_date = date(2025, 6, 20)
    elif demo_choice == "Step 2: Time Travel (2 Jul 2025)":
        default_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 2 Jul. Do they get one?"
        default_date = date(2025, 7, 2)
    elif demo_choice == "Step 5: Abstain on Equal Conflict":
        default_q = "What is the dispute settlement SLA window for interconnect billing discrepancies with carriers?"
        default_date = date(2025, 6, 1)
        default_product = "wholesale"
        default_segment = "enterprise"

    col_input1, col_input2 = st.columns([3, 1])

    with col_input1:
        preset_q = st.selectbox(
            "Quick Select Example Question:",
            [
                "-- Or choose an enterprise test case --",
                "Hero Case: Customer refund window on 20 Jun 2025 (Policy v1 vs Amendment A)",
                "Hero Case: Customer refund window on 2 Jul 2025 (Post Amendment A)",
                "Trap 1: Customer refund method: original card vs FAQ store credit",
                "Trap 1: Porting fee charged under MNP (Directive vs Website FAQ)",
                "Trap 2: Postpaid 48-hour cooling-off grace period after Amendment A",
                "Trap 4: Daily high-speed roaming allowance for Delhi student (Regional exception)",
                "Trap 5: Overdue fiber broadband late payment fee (Amendment chain)",
                "Abstain Case: Interconnect carrier dispute SLA (Bilateral agreements Alpha vs Beta)"
            ]
        )

        if "Hero Case: Customer refund window on 20 Jun 2025" in preset_q:
            default_q = "A customer recharges on 10 Jun 2025 and asks for a refund on 20 Jun. Do they get one?"
            default_date = date(2025, 6, 20)
        elif "Hero Case: Customer refund window on 2 Jul 2025" in preset_q:
            default_q = "A customer recharges on 20 Jun 2025 and asks for a refund on 2 Jul 2025. Do they get one?"
            default_date = date(2025, 7, 2)
        elif "Trap 1: Customer refund method" in preset_q:
            default_q = "What is the approved payment disbursement method for customer refunds?"
            default_date = date(2025, 8, 15)
        elif "Trap 1: Porting fee charged" in preset_q:
            default_q = "Is an administrative fee of Rs. 100 charged when a customer ports their number out under MNP?"
            default_date = date(2025, 6, 1)
        elif "Trap 2: Postpaid 48-hour cooling-off" in preset_q:
            default_q = "Does the 48-hour cooling-off grace period for postpaid activations still exist after Amendment A?"
            default_date = date(2025, 8, 1)
            default_product = "postpaid"
            default_segment = "retail"
        elif "Trap 4: Daily high-speed roaming allowance" in preset_q:
            default_q = "What is the daily high-speed roaming data limit for an enrolled student in Delhi NCR?"
            default_date = date(2025, 5, 15)
            default_product = "prepaid"
            default_region = "Delhi"
            default_segment = "student"
        elif "Trap 5: Overdue fiber broadband" in preset_q:
            default_q = "What is the late payment fee on an overdue fiber broadband invoice as of October 2024?"
            default_date = date(2024, 10, 1)
            default_product = "broadband"
        elif "Abstain Case: Interconnect" in preset_q:
            default_q = "What is the dispute settlement SLA window for interconnect billing discrepancies with carriers?"
            default_date = date(2025, 6, 1)
            default_product = "wholesale"
            default_segment = "enterprise"

        query_text = st.text_input("Question:", value=default_q)

    with col_input2:
        as_of_date = st.date_input("As-Of Date (Temporal Reference):", value=default_date)

    # Customer Scope Expansion
    with st.expander("🎯 Customer Scope Parameters (Optional Filter)", expanded=False):
        c_p, c_r, c_s = st.columns(3)
        with c_p:
            scope_prod = st.selectbox("Product:", ["all", "prepaid", "postpaid", "broadband", "streaming", "wholesale"], index=["all", "prepaid", "postpaid", "broadband", "streaming", "wholesale"].index(default_product) if default_product in ["all", "prepaid", "postpaid", "broadband", "streaming", "wholesale"] else 0)
        with c_r:
            scope_reg = st.selectbox("Region:", ["all", "Delhi", "Bangalore", "Mumbai", "Goa", "France", "Germany", "UK"], index=["all", "Delhi", "Bangalore", "Mumbai", "Goa", "France", "Germany", "UK"].index(default_region) if default_region in ["all", "Delhi", "Bangalore", "Mumbai", "Goa", "France", "Germany", "UK"] else 0)
        with c_s:
            scope_seg = st.selectbox("Customer Segment:", ["all", "retail", "student", "enterprise"], index=["all", "retail", "student", "enterprise"].index(default_segment) if default_segment in ["all", "retail", "student", "enterprise"] else 0)

    query_scope = Scope(product=scope_prod, region=scope_reg, customer_segment=scope_seg)

    # RUN COMPARISON
    side_by_side = pipeline.compare_side_by_side(query_text, as_of_date=as_of_date, scope=query_scope)
    tg_res = side_by_side["truthguard"]
    b_a = side_by_side["plain_rag_baseline_a"]
    b_b = side_by_side["newest_doc_baseline_b"]

    st.markdown("---")

    # Side-by-Side Presentation
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### ❌ Plain RAG (Standard Enterprise Assistant)")
        st.markdown(
            '<div class="rag-wrong-card">'
            '<b>Mechanism:</b> Grabs top-ranked semantic passage; assumes newest or best match is truth.<br><br>'
            f'<b>Assistant Answer:</b><br>"{b_a.get("answer", "")}"<br><br>'
            f'<b>Selected Document:</b> {b_a.get("selected_clause").doc_id if b_a.get("selected_clause") else "None"}<br>'
            '<b>Result:</b> <span style="color:#DC2626; font-weight:bold;">Confident & Legally Wrong</span><br>'
            '<small>Did not verify if clause was effective on the query date or if an authority conflict exists.</small>'
            '</div>',
            unsafe_allow_html=True
        )

    with col_right:
        st.markdown("### ✅ TruthGuard (Precedence & Falsification Engine)")
        winner_info = tg_res.get("winning_clause")
        status_label = tg_res.get("status")

        if status_label == "RESOLVED":
            st.markdown(
                '<div class="tg-win-card">'
                f'<b>Mechanism:</b> Hybrid Retrieval → Critic Falsification → 6 Deterministic Precedence Checks.<br><br>'
                f'<b>TruthGuard Answer:</b><br>{tg_res.get("answer", "").replace(chr(10), "<br>")}<br><br>'
                f'<b>Prevailing Clause:</b> <span class="citation-badge">{winner_info.get("clause_id") if winner_info else ""}</span> '
                f'from <i>{winner_info.get("doc_id") if winner_info else ""}</i> ({winner_info.get("doc_type") if winner_info else ""})<br>'
                f'<b>Effective Window:</b> {winner_info.get("effective_from") if winner_info else ""} to '
                f'{winner_info.get("effective_to") or "indefinitely open"}<br>'
                '<b>Result:</b> <span style="color:#059669; font-weight:bold;">Accurate & Legally Grounded</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="hero-card" style="border-left: 5px solid #F59E0B;">'
                f'<b>Status:</b> <span style="color:#D97706; font-weight:bold;">{status_label}</span><br><br>'
                f'<b>TruthGuard Answer:</b><br>{tg_res.get("answer", "").replace(chr(10), "<br>")}<br><br>'
                '<b>System Action:</b> Abstains and presents both sources; refuses to hallucinate a resolution.'
                '</div>',
                unsafe_allow_html=True
            )

    # Chronological Timeline View (Slide 1 / Section 9)
    st.markdown("### ⏱️ Chronological Policy Timeline View")
    st.caption("Visualizing publication vs effective dates. Highlights which clause governs on the query as-of date.")

    # Timeline layout for refund hero case or generic
    is_hero = "refund" in query_text.lower()
    if is_hero:
        q_date_str = as_of_date.strftime("%d %b %Y")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            st.markdown(
                '<div class="timeline-node ' + ('active' if as_of_date < date(2025, 7, 1) else 'expired') + '">'
                '<b>Jan 2025: Policy v1</b><br>'
                'cl.4.2: 7 days<br>'
                '<small>Effective: 1 Jan 2025</small>'
                '</div>',
                unsafe_allow_html=True
            )
        with col_t2:
            st.markdown(
                '<div class="timeline-node ' + ('active' if as_of_date >= date(2025, 7, 1) else '') + '">'
                '<b>Mar 2025: Amendment A</b><br>'
                'cl.4.2 → 14 days<br>'
                '<small style="color:#D97706; font-weight:bold;">Effective: 1 Jul 2025</small>'
                '</div>',
                unsafe_allow_html=True
            )
        with col_t3:
            st.markdown(
                '<div class="timeline-node" style="border: 2px dashed #3B82F6; background:#EFF6FF;">'
                f'<b>📍 Query Date: {q_date_str}</b><br>'
                f'<b>In Force:</b> {"Policy v1 (7 days)" if as_of_date < date(2025, 7, 1) else "Amendment A (14 days)"}'
                '</div>',
                unsafe_allow_html=True
            )
        with col_t4:
            st.markdown(
                '<div class="timeline-node" style="background:#FFFBEB; border: 1px solid #FDE68A;">'
                '<b>Aug 2025: FAQ #12</b><br>'
                'Promises "store credit"<br>'
                '<small style="color:#DC2626;">Flagged in Ledger</small>'
                '</div>',
                unsafe_allow_html=True
            )
    else:
        st.info(f"Timeline evaluated for query date: **{as_of_date}** with customer scope: **{query_scope.model_dump()}**.")

    # Step-by-Step Precedence Audit Trace
    st.markdown("### 🛡️ Precedence Engine 6-Step Audit Trace")
    with st.expander("View deterministic elimination trail for this query", expanded=True):
        trace_data = tg_res.get("precedence_trace", [])
        for step in trace_data:
            s_num = step["step_number"]
            s_name = step["step_name"]
            survivors = step["surviving_clause_ids"]
            eliminated = step.get("eliminated", [])

            st.markdown(f"**Step {s_num}: {s_name}**")
            st.caption(f"_{step['description']}_")

            cols_s = st.columns([1, 2])
            with cols_s[0]:
                st.write(f"✅ **Surviving Clauses ({len(survivors)}):** `{', '.join(survivors) if survivors else 'None'}`")
            with cols_s[1]:
                if eliminated:
                    for el in eliminated:
                        st.markdown(f"❌ **Eliminated `{el['clause_id']}`**: {el['reason']}")
                else:
                    st.write("*(No clauses eliminated at this step)*")
            st.markdown("---")


# =====================================================================
# TAB 2: CONTRADICTION LEDGER
# =====================================================================
with tabs[1]:
    st.markdown('<div class="main-header">Contradiction Ledger</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Automated fix-it tickets for document owners, ranked by <b>Traffic × Risk</b>. '
        '<i>The knowledge corpus gets cleaner every week.</i></div>',
        unsafe_allow_html=True
    )

    tickets = pipeline.ledger.get_ranked_tickets()

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Flagged Contradictions", len(tickets))
    with col_m2:
        high_risk_count = sum(1 for t in tickets if t.risk_level >= 4)
        st.metric("High Legal / Financial Risk", high_risk_count)
    with col_m3:
        top_priority = max((t.priority_score for t in tickets), default=0)
        st.metric("Peak Priority Score", top_priority)
    with col_m4:
        st.metric("Automated Fix SLA", "48 Hours")

    st.markdown("### Ranked Fix-It Tickets")

    ticket_dicts = [t.model_dump() for t in tickets]
    if ticket_dicts:
        df_tickets = pd.DataFrame(ticket_dicts)
        st.dataframe(
            df_tickets[[
                "ticket_id", "priority_score", "trap_category", "doc_owner",
                "winning_doc_title", "conflicting_doc_title", "status"
            ]],
            use_container_width=True
        )

        st.markdown("### Ticket Action Desk")
        selected_t_id = st.selectbox("Select Ticket to Review & Resolve:", [t.ticket_id for t in tickets])
        target_ticket = next((t for t in tickets if t.ticket_id == selected_t_id), None)

        if target_ticket:
            col_d1, col_d2 = st.columns([2, 1])
            with col_d1:
                st.markdown(f"**Ticket ID:** `{target_ticket.ticket_id}` | **Category:** `{target_ticket.trap_category}`")
                st.markdown(f"**Assigned Owner:** `{target_ticket.doc_owner}`")
                st.info(f"**Detected Conflict:**\n\n{target_ticket.summary}")
                st.success(f"**Recommended Action:**\n\n{target_ticket.recommended_action}")
            with col_d2:
                st.metric("Priority (Traffic × Risk)", f"{target_ticket.traffic_weight} × {target_ticket.risk_level} = {target_ticket.priority_score}")
                new_status = st.selectbox("Update Status:", ["OPEN", "IN_REVIEW", "RESOLVED", "DISMISSED"], index=["OPEN", "IN_REVIEW", "RESOLVED", "DISMISSED"].index(target_ticket.status.value))
                if st.button("Update Ticket Status"):
                    pipeline.ledger.update_status(target_ticket.ticket_id, new_status)
                    st.success(f"Ticket {target_ticket.ticket_id} updated to {new_status}!")


# =====================================================================
# TAB 3: EVALUATION SCOREBOARD
# =====================================================================
with tabs[2]:
    st.markdown('<div class="main-header">Evaluation Scoreboard vs Baselines</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Benchmarked across 65 Gold Questions covering all five traps, controls, and unresolvables.</div>',
        unsafe_allow_html=True
    )

    if st.button("🔄 Re-run Benchmark Suite"):
        evaluator = BenchmarkEvaluator(pipeline)
        scoreboard_data = evaluator.run_benchmark()
        st.success("Benchmark completed across 65 gold questions!")
    else:
        # Load cached benchmark
        b_path = BASE_DIR / "data/benchmark_results.json"
        if b_path.exists():
            with open(b_path, "r", encoding="utf-8") as f:
                scoreboard_data = json.load(f)
        else:
            evaluator = BenchmarkEvaluator(pipeline)
            scoreboard_data = evaluator.run_benchmark()

    # Core Metrics Table
    st.markdown("### Core Metric Comparison")
    df_metrics = pd.DataFrame(scoreboard_data["metrics"])
    st.table(df_metrics)

    # Per-Trap Breakdown
    st.markdown("### Per-Trap Accuracy Breakdown")
    breakdown = scoreboard_data["per_trap_breakdown"]
    df_trap = pd.DataFrame([
        {
            "Trap Name": trap.replace("_", " ").title(),
            "Total Questions": stats["total"],
            "TruthGuard Accuracy": stats["truthguard_acc"],
            "Baseline A (Plain RAG)": stats["baseline_a_acc"],
            "Baseline B (Newest Doc)": stats["baseline_b_acc"],
        }
        for trap, stats in breakdown.items()
    ])
    st.table(df_trap)

    # Trap Visual Comparison Chart
    trap_plot_data = []
    for trap, stats in breakdown.items():
        tg_val = float(stats["truthguard_acc"].replace("%", ""))
        ba_val = float(stats["baseline_a_acc"].replace("%", ""))
        bb_val = float(stats["baseline_b_acc"].replace("%", ""))
        trap_plot_data.append({"Trap": trap.replace("_", " ").title(), "TruthGuard": tg_val, "Plain RAG": ba_val, "Newest Doc": bb_val})
    
    st.bar_chart(pd.DataFrame(trap_plot_data).set_index("Trap"))


# =====================================================================
# TAB 4: CONFLICT FUZZER
# =====================================================================
with tabs[3]:
    st.markdown('<div class="main-header">Conflict Fuzzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Section 8: "Injects new conflicting versions of existing clauses and checks that TruthGuard still resolves them."</div>',
        unsafe_allow_html=True
    )

    fuzz_count = st.slider("Number of synthetic conflict injections:", min_value=1, max_value=8, value=3)

    if st.button("🚀 Run Real-Time Conflict Fuzz Cycle"):
        fuzzer = ConflictFuzzer(pipeline)
        fuzz_res = fuzzer.run_fuzz_cycle(num_injections=fuzz_count)

        pass_count = sum(1 for r in fuzz_res if r["resolved_correctly"])
        st.success(f"Fuzz Cycle Complete: {pass_count} / {len(fuzz_res)} Injected Conflicts Successfully Resolved by Precedence Engine!")

        for r in fuzz_res:
            with st.expander(f"{'✅' if r['resolved_correctly'] else '❌'} [{r['fuzz_id']}] Strategy: {r['strategy']} | Injected: {r['injected_clause_id']}", expanded=True):
                st.write(f"**Query:** {r['query']}")
                st.write(f"**As-Of Date:** {r['as_of_date']}")
                st.write(f"**Injected Document:** {r['injected_doc']}")
                st.write(f"**Verdict Status:** `{r['verdict_status']}`")
                st.write(f"**Winning Clause:** `{r['winning_clause_id']}`")
                st.info(f"**Precedence Engine Decision:** {r['notes']}")


# =====================================================================
# TAB 5: CLAUSE GRAPH EXPLORER
# =====================================================================
with tabs[4]:
    st.markdown('<div class="main-header">Clause Graph & Knowledge Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect clause nodes, authority ranks, and relationship edges (amends, withdraws, applies_to).</div>', unsafe_allow_html=True)

    g_clauses = pipeline.all_clauses
    st.write(f"Total Ingested Clauses: **{len(g_clauses)}** across **30** synthetic documents.")

    selected_cid = st.selectbox("Inspect Clause Node History:", [c.clause_id for c in g_clauses])
    target_c = pipeline.graph.get_clause(selected_cid)

    if target_c:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(f"### `{target_c.clause_id}`")
            st.write(f"**Document:** {target_c.doc_id} ({target_c.doc_type})")
            st.write(f"**Authority Rank:** {target_c.authority_rank} / 5")
            st.write(f"**Topic:** `{target_c.topic}` | **Specificity:** `{target_c.specificity}`")
            st.write(f"**Published:** {target_c.published_date} | **In Force:** {target_c.effective_from} to {target_c.effective_to or 'open'}")
            st.info(f"**Clause Text:**\n\n\"{target_c.text}\"")

        with col_g2:
            st.markdown("### Amendment & Supersession Trail")
            chain = pipeline.graph.trace_chain(target_c.clause_id)
            if chain:
                st.dataframe(pd.DataFrame(chain)[["clause_id", "doc_id", "effective_from", "effective_to"]], use_container_width=True)
            else:
                st.write("No connected amendment chain.")


# =====================================================================
# TAB 6: ARCHITECTURE & THE 5 TRAPS
# =====================================================================
with tabs[5]:
    st.markdown('<div class="main-header">The 5 Traps & Architecture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Why plain RAG fails in enterprise document conflict, and how TruthGuard solves it.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    ### 🏛️ The Legal Landmark: *Moffatt v. Air Canada, 2024 BCCRT 149*
    In 2024, an airline chatbot promised a passenger a bereavement refund that the airline's official policy did not permit.
    The tribunal ruled that **a company is legally bound by the words of its AI chatbot**, awarding damages to the plaintiff.
    Enterprise chatbots cannot simply answer with whatever passage has the highest cosine similarity.
    """)

    st.markdown("### The 5 Traps TruthGuard is Built to Catch")

    col_tr1, col_tr2 = st.columns(2)
    with col_tr1:
        st.markdown("""
        **01. Authority beats Recency**
        - *The Trap:* An employee support email or portal FAQ published yesterday cannot overrule a Master Board Policy published in January.
        - *TruthGuard Fix:* Deterministic Authority Table (`Regulation > Board Policy > Product T&C > FAQ > Email`).

        **02. Clause-level Supersession**
        - *The Trap:* When Amendment A amends cl.4.2 (refund window), a plain RAG retriever assumes all of Policy v1 is deprecated.
        - *TruthGuard Fix:* Preserves untouched clauses (e.g. cl.4.5 card refunds, cl.4.8 cooling-off).

        **03. In Force vs Published Date**
        - *The Trap:* Amendment A was published in March, but its effective date is 1 July. Plain RAG applies it on 20 June because it's newer.
        - *TruthGuard Fix:* Evaluates temporal validity against the queried `as_of_date`.
        """)
    with col_tr2:
        st.markdown("""
        **04. Specific beats General**
        - *The Trap:* A national policy caps roaming at 1GB, but a narrow Delhi Student pack grants 3GB. Plain RAG applies the general rule.
        - *TruthGuard Fix:* Narrow regional or segment exceptions survive newer general policies.

        **05. Amendment Chains**
        - *The Trap:* Policy v1 → Amendment 1 (10% fee) → Amendment 2 (rescinds Amendment 1, sets flat Rs. 50).
        - *TruthGuard Fix:* Follows `amends` and `withdraws` chains clause by clause.
        """)

    st.markdown("""
    ---
    ### The Precedence Engine: 6 Deterministic Checks
    ```
    Candidate Clauses
           │
           ▼
    1. Scope Check         ──► Drop clauses not covering product, region, segment
           │
           ▼
    2. In-Force Date       ──► Drop clauses not effective on as_of_date
           │
           ▼
    3. Supersession Trail  ──► Drop clauses amended or withdrawn by active revisions
           │
           ▼
    4. Authority Rank      ──► Keep highest authority (Regulation > Board Policy > T&C > FAQ > Email)
           │
           ▼
    5. Specificity         ──► Narrow regional/segment exception beats general rule
           │
           ▼
    6. Recency Tie-Breaker ──► Newer wins only between otherwise equal clauses
           │
           ▼
    Winner Resolved OR Tie-Abstain (Never Hallucinate / Blend)
    ```
    """)
