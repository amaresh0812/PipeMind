"""PipeMind: Data-Pipeline Failure Agent.
Streamlit application featuring memory-augmented diagnosis, side-by-side comparison,
and continuous learning via Hindsight.
"""
import os
import streamlit as st
from agent import BANK, HINDSIGHT_URL, PRIMARY, FALLBACK, diagnose, insights, record_outcome, today
from seed import INCIDENTS, seed_history

# Page configuration
st.set_page_config(
    page_title="PipeMind | Pipeline Failure Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern visual aesthetics
st.markdown(
    """
    <style>
    /* Global styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-memory-on {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #059669;
    }
    .badge-memory-off {
        background-color: #451a03;
        color: #fbbf24;
        border: 1px solid #d97706;
    }
    .card-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .memory-item {
        background: #0f172a;
        border-left: 3px solid #6366f1;
        padding: 0.75rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "diagnosis_result" not in st.session_state:
    st.session_state["diagnosis_result"] = None
if "last_failure" not in st.session_state:
    st.session_state["last_failure"] = None
if "feedback_status" not in st.session_state:
    st.session_state["feedback_status"] = None

# Preset Failures catalog (mix of schema drift, timeout, and null spike)
PRESET_FAILURES = {
    "[Schema Drift] orders_daily_load: KeyError 'payment_mode'": {
        "pipeline": "orders_daily_load",
        "error": "KeyError 'payment_mode' while reading orders_raw during daily ETL batch",
        "description": "Upstream service changed order schema without notifying downstream consumers.",
    },
    "[Schema Drift] orders_daily_load: KeyError 'tax_amount'": {
        "pipeline": "orders_daily_load",
        "error": "KeyError 'tax_amount': upstream ERP release renamed column during month-end run",
        "description": "Recurring month-end pattern where ERP deployment drops/renames tax fields.",
    },
    "[Timeout] sales_agg_hourly: ADF ActivityTimeout": {
        "pipeline": "sales_agg_hourly",
        "error": "ADF ActivityTimeout after 7200s: Synapse SQL pool paused or under-scaled at 02:00 UTC",
        "description": "ADF activity hung because the underlying Synapse SQL pool was paused or starved of compute.",
    },
    "[Null Spike] customer_dim_refresh: null_rate(email)=42%": {
        "pipeline": "customer_dim_refresh",
        "error": "DataQualityError null_rate(email)=42% > 5% threshold: CRM export truncated mid-file",
        "description": "Upstream CRM export stream cut off early, leaving blank records.",
    },
    "[Null Spike] customer_dim_refresh: null_rate(phone)=28%": {
        "pipeline": "customer_dim_refresh",
        "error": "DataQualityError null_rate(phone)=28% > 5% threshold: missing customer contact attributes",
        "description": "Partial CRM extraction failure resulting in failed Great Expectations data test.",
    },
    "[Custom Failure] Enter your own error details below": {
        "pipeline": "custom_pipeline",
        "error": "",
        "description": "Define a custom pipeline failure and test diagnosis.",
    },
}

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🧠 PipeMind Controls")
    st.markdown("Long-term memory for resilient data engineering.")

    # 1. Memory ON/OFF toggle
    memory_on = st.toggle("Memory ON/OFF", value=True, help="Enable or disable Hindsight memory retrieval during diagnosis.")

    # Status badge
    if memory_on:
        st.markdown('<span class="status-badge badge-memory-on">● Memory Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-memory-off">○ Memory Disabled (Generic LLM)</span>', unsafe_allow_html=True)

    st.markdown("---")

    # 6. Side-by-side mode toggle
    side_by_side = st.checkbox(
        "Side-by-side mode",
        value=False,
        help="Compare answers WITHOUT memory and WITH memory in two columns for the same failure.",
    )

    st.markdown("---")
    st.markdown("#### ⚡ Memory Bank Actions")

    # 1. Button "Seed history" (runs seed logic)
    if st.button("🌱 Seed history", use_container_width=True, help="Seeds initial 8 realistic incidents into Hindsight"):
        with st.spinner("Seeding history into Hindsight..."):
            try:
                count = seed_history()
                st.success(f"Retained {count} incidents into memory bank '{BANK}'!")
            except Exception as e:
                st.error(f"⚠️ Hindsight server error: {e}")

    # 1. "Team insights" button (shows insights() output)
    if st.button("📊 Team insights", use_container_width=True, help="Runs Hindsight reflect to summarize fragility, patterns, and fixes across all incidents"):
        with st.spinner("Reflecting on all past incidents across the memory bank..."):
            insight_text = insights()
            st.session_state["team_insights"] = insight_text

    if "team_insights" in st.session_state and st.session_state["team_insights"]:
        with st.expander("📈 Latest Team Insights", expanded=True):
            st.markdown(st.session_state["team_insights"])

    st.markdown("---")
    st.markdown("#### ⚙️ Configuration")
    st.caption(f"**Memory Bank:** `{BANK}`")
    st.caption(f"**Hindsight URL:** `{HINDSIGHT_URL}`")
    st.caption(f"**Groq Primary:** `{PRIMARY}`")
    st.caption(f"**Groq Fallback:** `{FALLBACK}`")


# ----------------- MAIN AREA -----------------
st.markdown('<div class="main-title">PipeMind: Data-Pipeline Failure Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">PipeMind REMEMBERS past pipeline incidents (and whether each fix worked) using Hindsight memory, so it diagnoses new failures with increasing precision.</div>',
    unsafe_allow_html=True,
)

# 2. Main Area: Dropdown of 5 preset failures plus free-text box for custom error
st.markdown("### 1. Select or Enter Pipeline Failure")
col_preset, col_when = st.columns([3, 1])

with col_preset:
    preset_choice = st.selectbox(
        "Select a preset incident or choose custom:",
        options=list(PRESET_FAILURES.keys()),
        index=0,
    )

with col_when:
    failure_date = st.text_input("Incident Date", value=today(), help="Date format YYYY-MM-DD")

selected_preset = PRESET_FAILURES[preset_choice]

# Editable fields pre-filled from preset
col_pipe, col_err = st.columns([1, 2])
with col_pipe:
    pipeline_name = st.text_input("Pipeline Name", value=selected_preset["pipeline"])
with col_err:
    error_text = st.text_area(
        "Error Message (Free-text box for custom error)",
        value=selected_preset["error"],
        height=100,
        placeholder="e.g. KeyError: 'cust_id' while running transform step...",
    )

# Current failure payload
current_failure = {
    "pipeline": pipeline_name.strip(),
    "when": failure_date.strip(),
    "error": error_text.strip(),
}

# 3. Button "Diagnose"
col_btn, _ = st.columns([1, 3])
with col_btn:
    diagnose_clicked = st.button("🔍 Diagnose Failure", type="primary", use_container_width=True)

if diagnose_clicked:
    if not current_failure["pipeline"] or not current_failure["error"]:
        st.warning("Please provide both a Pipeline Name and an Error Message.")
    else:
        st.session_state["last_failure"] = current_failure
        st.session_state["feedback_status"] = None

        if side_by_side:
            # 6. Side-by-side mode: compute both WITHOUT and WITH memory
            with st.spinner("Diagnosing WITHOUT memory (generic LLM) and WITH Hindsight memory..."):
                ans_no_mem, _ = diagnose(current_failure, use_memory=False)
                ans_with_mem, recalled_memories = diagnose(current_failure, use_memory=True)
                st.session_state["diagnosis_result"] = {
                    "mode": "side_by_side",
                    "ans_no_mem": ans_no_mem,
                    "ans_with_mem": ans_with_mem,
                    "memories": recalled_memories,
                }
        else:
            with st.spinner(f"Diagnosing failure ({'with Hindsight memory' if memory_on else 'without memory'})..."):
                ans, recalled_memories = diagnose(current_failure, use_memory=memory_on)
                st.session_state["diagnosis_result"] = {
                    "mode": "single",
                    "answer": ans,
                    "memories": recalled_memories,
                    "memory_on": memory_on,
                }

# Render diagnosis if available
if st.session_state["diagnosis_result"]:
    result = st.session_state["diagnosis_result"]
    st.markdown("---")
    st.markdown("### 2. Diagnosis Output")

    if result["mode"] == "side_by_side":
        # 6. Side-by-side comparison mode
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### ❌ WITHOUT Memory (Generic LLM)")
            st.info(result["ans_no_mem"])
            st.caption("Generic diagnosis relying solely on static model pre-training.")

        with col_right:
            st.markdown("#### ✅ WITH Hindsight Memory (Context-Aware)")
            st.success(result["ans_with_mem"])
            st.caption("Contextual diagnosis informed by past team incidents and verified fixes.")

            # 4. Collapsible panel "Memories used"
            with st.expander(f"📚 Memories used ({len(result['memories'])} recalled)", expanded=True):
                if result["memories"]:
                    for mem in result["memories"]:
                        if mem.startswith("[Hindsight server offline"):
                            st.warning(mem)
                        else:
                            st.markdown(f'<div class="memory-item">{mem}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No prior incidents recalled for this failure.")

    else:
        # Standard Single Diagnosis Mode
        header_text = "Diagnosis (Memory: ON)" if result["memory_on"] else "Diagnosis (Memory: OFF)"
        st.markdown(f"#### {header_text}")
        if result["memory_on"]:
            st.success(result["answer"])
        else:
            st.info(result["answer"])

        # 4. Collapsible panel "Memories used" listing what recall returned
        if result["memory_on"]:
            with st.expander(f"📚 Memories used ({len(result['memories'])} recalled)", expanded=False):
                if result["memories"]:
                    for mem in result["memories"]:
                        if mem.startswith("[Hindsight server offline"):
                            st.warning(mem)
                        else:
                            st.markdown(f'<div class="memory-item">{mem}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No prior incidents recalled from Hindsight memory bank.")

    # 5. After the answer: text input for resolution + two buttons "Fix worked" and "Fix did not work"
    st.markdown("---")
    st.markdown("### 3. Record Resolution Outcome (Teach PipeMind)")
    st.markdown("Document the attempted resolution to build long-term institutional intelligence.")

    resolution_input = st.text_input(
        "Resolution attempted:",
        value="Added column alias mapping in the ingest transform step and verified downstream tables.",
        key="resolution_input_field",
        help="Describe what action was taken so future incidents can cite or avoid this fix.",
    )

    col_worked, col_failed, _ = st.columns([1, 1, 2])

    with col_worked:
        if st.button("✅ Fix worked", use_container_width=True):
            if not resolution_input.strip():
                st.warning("Please describe the resolution attempted before recording.")
            else:
                ok = record_outcome(
                    st.session_state["last_failure"] or current_failure,
                    resolution_input.strip(),
                    worked=True,
                )
                if ok:
                    st.session_state["feedback_status"] = ("success", "Recorded: Fix WORKED! PipeMind will prioritize this solution for similar failures.")
                else:
                    st.session_state["feedback_status"] = ("error", f"Could not record outcome: Hindsight server is offline at {HINDSIGHT_URL}.")

    with col_failed:
        if st.button("❌ Fix did not work", use_container_width=True):
            if not resolution_input.strip():
                st.warning("Please describe the resolution attempted before recording.")
            else:
                ok = record_outcome(
                    st.session_state["last_failure"] or current_failure,
                    resolution_input.strip(),
                    worked=False,
                )
                if ok:
                    st.session_state["feedback_status"] = ("warning", "Recorded: Fix DID NOT WORK! PipeMind will warn against repeating this attempt.")
                else:
                    st.session_state["feedback_status"] = ("error", f"Could not record outcome: Hindsight server is offline at {HINDSIGHT_URL}.")


    if st.session_state["feedback_status"]:
        status_type, msg = st.session_state["feedback_status"]
        if status_type == "success":
            st.success(msg)
        elif status_type == "warning":
            st.warning(msg)
        else:
            st.error(msg)
