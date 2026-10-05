import json
import os
import streamlit as st

from incident_agent import (
    IncidentState,
    diagnose_node,
    propose_fix_node,
    log_step,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Incident Response AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    /* =========================
       MAIN APP
       ========================= */

    .stApp {
        background-color: #0b1120;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* =========================
       HEADER
       ========================= */

    .title {
        font-size: 32px;
        font-weight: 750;
        color: #f8fafc;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* =========================
       STATUS
       ========================= */

    .online {
        display: inline-block;
        padding: 7px 13px;
        border-radius: 20px;
        background-color: #052e16;
        border: 1px solid #166534;
        color: #86efac;
        font-size: 12px;
        font-weight: 600;
    }

    /* =========================
       RESULT BOX
       ========================= */

    .diagnosis-box {
        background-color: #0f1b32;
        border: 1px solid #1d4ed8;
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 16px;
        color: #dbeafe;
        line-height: 1.7;
        font-size: 14px;
        word-wrap: break-word;
        overflow-wrap: anywhere;
    }

    .fix-box {
        background-color: #211b0d;
        border: 1px solid #92400e;
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 16px;
        color: #fef3c7;
        line-height: 1.7;
        font-size: 14px;
        word-wrap: break-word;
        overflow-wrap: anywhere;
    }

    /* =========================
       AUDIT TIMELINE
       ========================= */

    .audit-step {
        color: #60a5fa;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .audit-detail {
        color: #cbd5e1;
        font-size: 13px;
        line-height: 1.6;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        white-space: normal;
    }

    /* =========================
       SIDEBAR
       ========================= */

    section[data-testid="stSidebar"] {
        background-color: #080d19;
    }

    /* =========================
       BUTTONS
       ========================= */

    .stButton > button {
        min-height: 42px;
        border-radius: 9px;
        font-weight: 650;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "incident_state" not in st.session_state:
    st.session_state.incident_state = None


# ============================================================
# HELPER: CREATE STATE
# ============================================================

def create_initial_state(report: str) -> IncidentState:

    return {
        "incident_report": report,
        "diagnosis": None,
        "proposed_fix": None,
        "confidence": None,
        "approved": None,
        "execution_result": None,
        "audit_trail": [],
    }


# ============================================================
# HELPER: SAVE LOG
# ============================================================

def save_incident_log(state: IncidentState):

    file_path = "incident_log.json"

    logs = []

    if os.path.exists(file_path):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:

                logs = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):

            logs = []

    logs.append(
        {
            "incident_report": state["incident_report"],
            "diagnosis": state["diagnosis"],
            "proposed_fix": state["proposed_fix"],
            "confidence": state["confidence"],
            "approved": state["approved"],
            "execution_result": state["execution_result"],
            "audit_trail": state["audit_trail"],
        }
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            logs,
            file,
            indent=2,
        )


# ============================================================
# HELPER: EXECUTE FIX
# ============================================================

def execute_fix(state: IncidentState):

    if state["approved"] is True:

        result = (
            f"Executed fix: "
            f"{state['proposed_fix']}"
        )

    else:

        result = (
            "Fix rejected by human reviewer. "
            "No action taken."
        )

    state["execution_result"] = result

    log_step(
        state,
        "execute",
        result,
    )

    save_incident_log(state)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚡ Incident AI")

    st.caption(
        "Autonomous Incident Response Dashboard"
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🚨 Incident Console",
            "📊 Evaluation",
            "📋 Audit Logs",
        ],
    )

    st.divider()

    st.caption("Architecture")

    st.write("LangGraph orchestration")
    st.write("Groq LLM reasoning")
    st.write("Human-in-the-loop approval")
    st.write("JSON audit persistence")

    st.divider()

    # Clear history button
    if page == "📋 Audit Logs":

        if st.button(
            "🗑️ Clear Audit History",
            use_container_width=True,
        ):

            if os.path.exists(
                "incident_log.json"
            ):

                os.remove(
                    "incident_log.json"
                )

                st.success(
                    "Audit history cleared."
                )

                st.rerun()


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.markdown(
        '<div class="title">⚡ Incident Response AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitle">
        AI-powered SRE diagnosis, remediation and
        human-in-the-loop execution.
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:

    st.markdown(
        '<div class="online">● SYSTEM ONLINE</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# INCIDENT CONSOLE
# ============================================================

if page == "🚨 Incident Console":

    st.markdown("## 🚨 Incident Console")

    st.caption(
        "Submit a production incident and let the AI analyze it."
    )

    # --------------------------------------------------------
    # DEFAULT INCIDENT
    # --------------------------------------------------------

    default_incident = (
        "ALERT: payments-service p99 latency spiked to 4200ms "
        "(baseline 180ms). "
        "Error logs show: 'connection pool exhausted' repeated "
        "340 times in last 5 minutes. "
        "DB CPU utilization at 92%. "
        "No recent deployments in last 2 hours."
    )

    incident_report = st.text_area(
        "Incident Report",
        value=default_incident,
        height=180,
        placeholder="Paste incident details here...",
    )

    if st.button(
        "🔍 Analyze Incident",
        type="primary",
        use_container_width=True,
    ):

        if not incident_report.strip():

            st.error(
                "Please enter an incident report."
            )

        else:

            state = create_initial_state(
                incident_report.strip()
            )

            try:

                with st.spinner(
                    "🧠 Diagnosing incident..."
                ):

                    state = diagnose_node(state)

                with st.spinner(
                    "🔧 Generating remediation..."
                ):

                    state = propose_fix_node(state)

                st.session_state.incident_state = state

                st.success(
                    "Incident analysis completed."
                )

            except Exception as error:

                st.error(
                    "Agent execution failed."
                )

                st.exception(error)

    # --------------------------------------------------------
    # CURRENT STATE
    # --------------------------------------------------------

    state = st.session_state.incident_state

    if state is not None:

        st.divider()

        confidence = (
            state["confidence"]
            if state["confidence"] is not None
            else 0.0
        )

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # ====================================================
        # METRICS
        # ====================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "AI Confidence",
                f"{confidence:.0%}",
            )

        with col2:

            st.metric(
                "Pipeline",
                "Analysis Complete",
            )

        with col3:

            if state["approved"] is None:

                approval = "Pending"

            elif state["approved"]:

                approval = "Approved"

            else:

                approval = "Rejected"

            st.metric(
                "Human Approval",
                approval,
            )

        st.divider()

        # ====================================================
        # DIAGNOSIS / FIX
        # ====================================================

        left, right = st.columns(
            2,
            gap="large",
        )

        with left:

            st.markdown(
                "### 🧠 Root Cause Analysis"
            )

            diagnosis = (
                state["diagnosis"]
                or "No diagnosis generated."
            )

            st.markdown(
                f"""
                <div class="diagnosis-box">
                {diagnosis}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                "### 🔧 Proposed Fix"
            )

            proposed_fix = (
                state["proposed_fix"]
                or "No fix proposed."
            )

            st.markdown(
                f"""
                <div class="fix-box">
                {proposed_fix}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.progress(
                confidence,
                text=f"Confidence: {confidence:.0%}",
            )

        st.divider()

        # ====================================================
        # HUMAN APPROVAL
        # ====================================================

        if state["approved"] is None:

            st.markdown(
                "### 👤 Human Approval Gate"
            )

            st.caption(
                "The remediation will execute only after explicit approval."
            )

            if confidence < 0.60:

                st.warning(
                    "⚠️ Low confidence remediation. "
                    "Human review is strongly recommended."
                )

            approve_col, reject_col = st.columns(
                2,
                gap="medium",
            )

            with approve_col:

                if st.button(
                    "✅ Approve & Execute",
                    type="primary",
                    use_container_width=True,
                ):

                    state["approved"] = True

                    log_step(
                        state,
                        "human_approval",
                        "approved=True",
                    )

                    execute_fix(state)

                    st.session_state.incident_state = state

                    st.rerun()

            with reject_col:

                if st.button(
                    "❌ Reject Fix",
                    use_container_width=True,
                ):

                    state["approved"] = False

                    log_step(
                        state,
                        "human_approval",
                        "approved=False",
                    )

                    execute_fix(state)

                    st.session_state.incident_state = state

                    st.rerun()

        # ====================================================
        # EXECUTION RESULT
        # ====================================================

        if state["execution_result"]:

            st.divider()

            st.markdown(
                "### ⚡ Execution Result"
            )

            if state["approved"]:

                st.success(
                    state["execution_result"]
                )

            else:

                st.warning(
                    state["execution_result"]
                )

        # ====================================================
        # AUDIT TRAIL
        # ====================================================

        st.divider()

        st.markdown(
            "### 📋 Current Incident Timeline"
        )

        st.caption(
            "Steps performed during this incident."
        )

        audit_trail = state.get(
            "audit_trail",
            [],
        )

        if not audit_trail:

            st.info(
                "No audit events yet."
            )

        else:

            for number, item in enumerate(
                audit_trail,
                start=1,
            ):

                with st.container(
                    border=True
                ):

                    step_name = str(
                        item.get(
                            "step",
                            "UNKNOWN",
                        )
                    ).upper()

                    detail = item.get(
                        "detail",
                        "",
                    )

                    timestamp = item.get(
                        "timestamp",
                        "",
                    )

                    st.markdown(
                        f"**{number}. {step_name}**"
                    )

                    st.write(
                        detail
                    )

                    st.caption(
                        timestamp
                    )


# ============================================================
# EVALUATION
# ============================================================

elif page == "📊 Evaluation":

    st.markdown(
        "## 📊 Agent Evaluation"
    )

    st.caption(
        "Results generated by the existing eval.py."
    )

    file_path = "eval_results.json"

    if not os.path.exists(file_path):

        st.info(
            "No evaluation results found."
        )

        st.code(
            "python eval.py"
        )

    else:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:

                results = json.load(file)

            if not results:

                st.info(
                    "Evaluation file is empty."
                )

            else:

                total = len(results)

                confidence_values = [
                    float(
                        item.get(
                            "confidence",
                            0,
                        ) or 0
                    )
                    for item in results
                ]

                average = (
                    sum(confidence_values)
                    / total
                )

                high_confidence = sum(
                    1
                    for value in confidence_values
                    if value >= 0.60
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Incidents Tested",
                        total,
                    )

                with col2:

                    st.metric(
                        "Average Confidence",
                        f"{average:.2f}",
                    )

                with col3:

                    st.metric(
                        "Confidence ≥ 60%",
                        f"{high_confidence}/{total}",
                    )

                st.divider()

                st.markdown(
                    "### Evaluation Results"
                )

                st.dataframe(
                    results,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as error:

            st.error(
                "Could not read eval_results.json."
            )

            st.exception(error)


# ============================================================
# AUDIT LOGS
# ============================================================

elif page == "📋 Audit Logs":

    st.markdown(
        "## 📋 Incident History"
    )

    st.caption(
        "Historical incidents saved by the response system."
    )

    file_path = "incident_log.json"

    if not os.path.exists(file_path):

        st.info(
            "No incidents have been recorded yet."
        )

    else:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:

                logs = json.load(file)

            if not logs:

                st.info(
                    "Audit history is empty."
                )

            else:

                # =================================================
                # SUMMARY
                # =================================================

                total = len(logs)

                approved_count = sum(
                    1
                    for log in logs
                    if log.get("approved") is True
                )

                rejected_count = sum(
                    1
                    for log in logs
                    if log.get("approved") is False
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Total Incidents",
                        total,
                    )

                with col2:

                    st.metric(
                        "Approved",
                        approved_count,
                    )

                with col3:

                    st.metric(
                        "Rejected",
                        rejected_count,
                    )

                st.divider()

                # =================================================
                # INCIDENT CARDS
                # =================================================

                for reverse_index, log in enumerate(
                    reversed(logs),
                    start=1,
                ):

                    incident_number = (
                        total
                        - reverse_index
                        + 1
                    )

                    approved = log.get(
                        "approved"
                    )

                    if approved is True:

                        status = "APPROVED"

                    elif approved is False:

                        status = "REJECTED"

                    else:

                        status = "PENDING"

                    confidence = (
                        log.get(
                            "confidence",
                            0,
                        )
                        or 0
                    )

                    # ---------------------------------------------
                    # EXPANDER HEADER
                    # ---------------------------------------------

                    with st.expander(
                        f"🚨 Incident #{incident_number}  •  {status}  •  Confidence {float(confidence):.0%}",
                        expanded=(reverse_index == 1),
                    ):

                        # -----------------------------------------
                        # INCIDENT
                        # -----------------------------------------

                        st.markdown(
                            "### 🚨 Incident Report"
                        )

                        # st.write automatically wraps text.
                        # No st.code() here, therefore no
                        # horizontal scrollbar.

                        st.write(
                            log.get(
                                "incident_report",
                                "N/A",
                            )
                        )

                        # -----------------------------------------
                        # DIAGNOSIS
                        # -----------------------------------------

                        st.markdown(
                            "### 🧠 Root Cause"
                        )

                        st.write(
                            log.get(
                                "diagnosis",
                                "N/A",
                            )
                        )

                        # -----------------------------------------
                        # FIX
                        # -----------------------------------------

                        st.markdown(
                            "### 🔧 Proposed Fix"
                        )

                        st.write(
                            log.get(
                                "proposed_fix",
                                "N/A",
                            )
                        )

                        # -----------------------------------------
                        # STATUS ROW
                        # -----------------------------------------

                        st.markdown(
                            "### 📊 Incident Status"
                        )

                        status_col1, status_col2 = st.columns(2)

                        with status_col1:

                            st.metric(
                                "Confidence",
                                f"{float(confidence):.0%}",
                            )

                        with status_col2:

                            st.metric(
                                "Approval",
                                status,
                            )

                        # -----------------------------------------
                        # EXECUTION
                        # -----------------------------------------

                        st.markdown(
                            "### ⚡ Execution Result"
                        )

                        execution = log.get(
                            "execution_result",
                            "N/A",
                        )

                        if approved is True:

                            st.success(
                                execution
                            )

                        elif approved is False:

                            st.warning(
                                execution
                            )

                        else:

                            st.info(
                                execution
                            )

                        # -----------------------------------------
                        # TIMELINE
                        # -----------------------------------------

                        st.markdown(
                            "### 📋 Audit Timeline"
                        )

                        audit_trail = log.get(
                            "audit_trail",
                            [],
                        )

                        if not audit_trail:

                            st.info(
                                "No audit events recorded."
                            )

                        else:

                            for step_number, item in enumerate(
                                audit_trail,
                                start=1,
                            ):

                                with st.container(
                                    border=True
                                ):

                                    step_name = str(
                                        item.get(
                                            "step",
                                            "UNKNOWN",
                                        )
                                    ).upper()

                                    detail = item.get(
                                        "detail",
                                        "",
                                    )

                                    timestamp = item.get(
                                        "timestamp",
                                        "",
                                    )

                                    st.markdown(
                                        f"**{step_number}. {step_name}**"
                                    )

                                    st.write(
                                        detail
                                    )

                                    st.caption(
                                        timestamp
                                    )

        except Exception as error:

            st.error(
                "Could not read incident_log.json."
            )

            st.exception(error)