"""
Automation Page
===============
Routing, model choice, and parallel execution guidance.
"""
import streamlit as st

from dashboard.data.routing import TASK_PROFILES, recommend_execution_plan, build_agent_flow
from dashboard.data.settings import load_settings, save_settings
from dashboard.services import get_service_status, get_service_status_snapshot
from dashboard.ui.components import section_header, card, chip


def render():
    """Render automation and orchestration guidance."""
    settings = load_settings()
    status = get_service_status_snapshot(include_optional=False, include_model_details=False)

    section_header(
        "Automation",
        "How tasks are routed, queued, and surfaced back to you",
        [("Plug and Play", "ready"), ("Parallel Aware", "info"), ("Model Smart", "ready")],
    )

    controls = st.columns([2, 2, 1])
    with controls[0]:
        task_key = st.selectbox(
            "Task type",
            list(TASK_PROFILES.keys()),
            format_func=lambda key: TASK_PROFILES[key]["label"],
        )
    with controls[1]:
        active_projects = st.selectbox(
            "Active projects",
            [1, 2, 3, 4],
            index=0,
            help="This is the number of repos you expect to be actively queued or reviewed at once.",
        )
    with controls[2]:
        allow_paid = st.toggle(
            "Allow paid",
            value=bool(settings.get("autoRouting", True)),
            help="When enabled, the router can recommend paid planning/review lanes if keys are ready.",
        )

    if st.button("↻ Refresh routing signals", use_container_width=True):
        status = get_service_status(force_refresh=True)
        st.session_state["automation_status_refreshed"] = True
        st.rerun()

    plan = recommend_execution_plan(task_key, active_projects, status, allow_paid=allow_paid)
    flow = build_agent_flow(plan)

    st.markdown("### 🚦 Recommended Route")
    cols = st.columns(4)
    with cols[0]:
        card("Chosen Model", plan["chosen_model"], plan["task_label"], "ready" if "No ready model" not in plan["chosen_model"] else "danger", "🧠")
    with cols[1]:
        card("Routing Mode", plan["route_label"], plan["reason"], "info", "🛰️")
    with cols[2]:
        card("Parallelism", str(plan["recommended_concurrency"]), plan["lane_mode"], "warn" if plan["recommended_concurrency"] > 1 else "ready", "🧵")
    with cols[3]:
        card("Paid Ready", str(plan["paid_ready_count"]), "Providers with live keys", "info", "💳")

    st.markdown("### 🧩 What This Means")
    st.markdown(f'<div class="insight-panel">{plan["speed_note"]}</div>', unsafe_allow_html=True)
    st.caption(plan["fallback"])
    st.caption("Routing advice uses last known machine status so this page stays instant.")

    st.markdown("### 🔀 Agent Flow")
    flow_cols = st.columns(len(flow))
    for idx, step in enumerate(flow):
        with flow_cols[idx]:
            st.markdown(
                f"""
                <div class="flow-lane lane-{step['tone']}">
                    <div class="flow-title">{step['title']}</div>
                    <div class="flow-detail">{step['detail']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 👀 User Experience")
    experience_lines = [
        "The dashboard should feel instant on Home because deep checks and live model details stay on focused pages.",
        "One active local model means one main coding lane. Extra projects should queue cleanly instead of pretending to be parallel.",
        "Paid routing is best used as a planner or reviewer lane while local models keep implementation cheap.",
        "Logs, reports, and validation should be shown as outputs of a lane, not hidden in disconnected pages.",
    ]
    st.markdown('<div class="diagnostic-panel"><ul class="status-list">', unsafe_allow_html=True)
    for line in experience_lines:
        st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
    st.markdown("</ul></div>", unsafe_allow_html=True)

    st.markdown("### ⚙️ Automation Defaults")
    auto_routing = st.toggle(
        "Automatically recommend the best model",
        value=bool(settings.get("autoRouting", True)),
        help="This affects dashboard guidance and future routing-oriented UI decisions.",
    )
    if st.button("Save automation defaults", type="primary"):
        new_settings = settings.copy()
        new_settings["autoRouting"] = auto_routing
        save_settings(new_settings)
        st.success("Automation defaults updated.")
        st.rerun()
