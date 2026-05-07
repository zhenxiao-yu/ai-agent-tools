"""
Home Page
=========
Dashboard home with service status and quick actions.
"""
from datetime import datetime
import re

import streamlit as st

from dashboard.cache import invalidate_cache
from dashboard.config import LOGS
from dashboard.data.allowlist import read_allowlist
from dashboard.data.routing import recommend_execution_plan
from dashboard.services import (
    describe_service_status_snapshot,
    ensure_service_status_snapshot_fresh,
    get_service_status,
    get_service_status_snapshot,
)
from dashboard.ui.components import section_header, card, quick_action, info_panel
from dashboard.utils import latest_files, file_preview, today_count, recent_dashboard_events


def render():
    """Render home page."""
    section_header(
        "Dashboard",
        "System overview and quick actions",
        [("Free Local", "ready"), ("Stable", "info")]
    )

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    actions = [
        ("🚀 Start Stack", "start-local-model-stack.ps1", "Start local AI stack"),
        ("🔍 Health Check", "doctor-local-ai.ps1", "Run diagnostics"),
        ("📝 Open VS Code", "open-ai-tools-vscode.ps1", "Open workspace"),
        ("📊 Monitor", "ai-stack-monitor.ps1", "Monitor resources"),
    ]

    for row_start in range(0, len(actions), 2):
        cols = st.columns(2)
        for col_index, (label, script, help_text) in enumerate(actions[row_start:row_start + 2]):
            with cols[col_index]:
                quick_action(label, script, help_text=help_text)
    if st.button("🔄 Refresh dashboard", help="Refresh cached service and settings state", use_container_width=True):
        invalidate_cache()
        get_service_status(force_refresh=True)
        st.rerun()

    # Service Status
    status = get_service_status_snapshot(include_model_details=False)
    ensure_service_status_snapshot_fresh(include_model_details=False)
    st.caption(describe_service_status_snapshot(status))
    repos = read_allowlist()
    plan = recommend_execution_plan("quick_fix", max(1, min(len(repos), 3)), status, allow_paid=False)

    # Count failures today
    failures_today = 0
    for p in latest_files(LOGS, 80, "*.log"):
        if datetime.fromtimestamp(p.stat().st_mtime).date() == datetime.now().date():
            preview = file_preview(p, 2500)
            if re.search(r"\b(ERROR|FAIL|failed)\b", preview, re.I):
                failures_today += 1

    warnings = []
    if status.get("snapshot_ready") and not status["ollama"]:
        warnings.append("Ollama is offline, so local coding runs will not start.")
    if status.get("snapshot_ready") and not status["proxy"]:
        warnings.append("The free Claude-compatible proxy is offline.")
    if status.get("errors"):
        warnings.append(f"{len(status['errors'])} background checks degraded; open diagnostics below.")

    if warnings:
        st.markdown('<div class="diagnostic-panel"><strong>Attention needed</strong><ul class="status-list">', unsafe_allow_html=True)
        for item in warnings:
            st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

    # Status Cards - Row 1
    st.markdown("### 🎯 Service Status")
    cols = st.columns(4)

    with cols[0]:
        if status.get("snapshot_ready"):
            card("Local AI", "Ready" if status["ollama"] else "Offline",
                 "Ollama API", "ready" if status["ollama"] else "danger", "🤖")
        else:
            card("Local AI", "Checking", "Background snapshot warming up", "info", "🤖")
    with cols[1]:
        has_model = "qwen2.5-coder:14b" in status.get("models", "")
        if not status.get("snapshot_ready"):
            card("Default Model", "Pending", "Waiting for runtime snapshot", "info", "🧠")
        elif status["ollama"] and not status.get("models"):
            card("Default Model", "Check Models page", "Deferred for faster load", "info", "🧠")
        else:
            card("Default Model", "Available" if has_model else "Missing",
                 "qwen2.5-coder:14b", "ready" if has_model else "warn", "🧠")
    with cols[2]:
        gpu = "GPU" in status.get("ps", "")
        if status.get("snapshot_ready"):
            gpu_label = "Active" if gpu else "Unknown"
            gpu_detail = "Open Models page for live runtime details"
            card("GPU", gpu_label, gpu_detail, "ready" if gpu else "info", "🎮")
        else:
            card("GPU", "Pending", "Waiting for runtime snapshot", "info", "🎮")
    with cols[3]:
        if status.get("snapshot_ready"):
            card("Proxy", "Online" if status["proxy"] else "Offline",
                 "free-claude-code", "ready" if status["proxy"] else "warn", "🔗")
        else:
            card("Proxy", "Checking", "Background snapshot warming up", "info", "🔗")

    # Status Cards - Row 2
    cols = st.columns(4)
    with cols[0]:
        card("Dashboard", "Online", "http://localhost:8501", "ready", "📊")
    with cols[1]:
        if status.get("snapshot_ready"):
            card("GitHub", "Connected" if status["github"] else "Not Connected",
                 "CLI auth", "ready" if status["github"] else "warn", "🐙")
        else:
            card("GitHub", "Checking", "Background snapshot warming up", "info", "🐙")
    with cols[2]:
        if status.get("snapshot_ready"):
            card("Scheduler", "Enabled" if status["scheduled"] else "Disabled",
                 "Local only", "warn" if status["scheduled"] else "muted", "⏰")
        else:
            card("Scheduler", "Checking", "Background snapshot warming up", "info", "⏰")
    with cols[3]:
        card("Projects", str(len(repos)), "Repositories", "info", "📁")

    st.markdown("### 🧠 Plug-and-Play Workflow")
    cols = st.columns(3)
    with cols[0]:
        info_panel("1. Pick a Lane", "Home stays fast. Use Automation to preview routing and Models only when you need deeper runtime details.", "info")
    with cols[1]:
        info_panel("2. Let It Queue", f"Recommended default route is `{plan['chosen_model']}` with {plan['lane_mode'].lower()}.", "ready")
    with cols[2]:
        info_panel("3. Review Outputs", "Workers should surface logs, validation, and reports as results of a run, not hidden side effects.", "ready")

    # Activity
    st.markdown("### 📈 Activity")
    runs = today_count(LOGS, "web-ai-*.log")
    cols = st.columns(2)
    with cols[0]:
        card("Runs Today", str(runs), "Worker executions", "info", "▶️")
    with cols[1]:
        card("Failures", str(failures_today), "Errors detected",
             "danger" if failures_today else "ready", "⚠️")

    # Recommendations
    st.markdown("### 💡 Next Steps")
    if not repos:
        st.info("**Add your first project**\n\nThe system needs one explicit repo path.")
    elif failures_today > 0:
        st.warning("**Check Fix Center**\n\nThere are issues that need attention.")
    else:
        st.success("**All systems ready**\n\nRun a dry-run on any project to start.")

    st.markdown("### 🔀 Multi-Project Impact")
    impact_cols = st.columns(3)
    with impact_cols[0]:
        card("Routing Advice", plan["route_label"], plan["reason"], "info", "🛰️")
    with impact_cols[1]:
        card("Parallel Lanes", str(plan["recommended_concurrency"]), plan["lane_mode"], "warn" if plan["recommended_concurrency"] > 1 else "ready", "🧵")
    with impact_cols[2]:
        card("Speed Impact", "Queue grows" if len(repos) > 1 else "Stable", plan["speed_note"], "warn" if len(repos) > 1 else "ready", "⚡")

    with st.expander("🧪 Diagnostics and recent dashboard logs"):
        if status.get("errors"):
            st.markdown("**Degraded checks**")
            st.code("\n".join(status["errors"]), language="text")
        events = recent_dashboard_events(25)
        if events:
            st.markdown("**Recent events**")
            st.code("\n".join(events), language="text")
        latest = latest_files(LOGS, 1, "dashboard*.log")
        if latest:
            st.markdown(f"**Latest dashboard log:** `{latest[0].name}`")
            st.code(file_preview(latest[0], 6000), language="text")
