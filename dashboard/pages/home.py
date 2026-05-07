"""
Home Page
=========
Dashboard home with service status and quick actions.
"""
from datetime import datetime

import streamlit as st

from cache import invalidate_cache
from config import PAGE_ICONS
from data.allowlist import read_allowlist
from data.settings import load_settings
from services import get_service_status
from ui.components import section_header, card, quick_action, action_result
from utils import latest_files, file_preview, today_count
import re


def render():
    """Render home page."""
    section_header(
        "Dashboard",
        "System overview and quick actions",
        [("Free Local", "ready"), ("Stable", "info")]
    )

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    cols = st.columns(5)
    actions = [
        ("🚀 Start Stack", "start-local-model-stack.ps1", "Start local AI stack"),
        ("🔍 Health Check", "doctor-local-ai.ps1", "Run diagnostics"),
        ("📝 Open VS Code", "open-ai-tools-vscode.ps1", "Open workspace"),
        ("📊 Monitor", "ai-stack-monitor.ps1", "Monitor resources"),
    ]

    for i, (label, script, help_text) in enumerate(actions):
        with cols[i]:
            quick_action(label, script, help_text=help_text)

    with cols[4]:
        if st.button("🔄 Refresh", help="Refresh dashboard"):
            invalidate_cache()
            st.rerun()

    # Service Status
    status = get_service_status()
    repos = read_allowlist()

    # Count failures today
    failures_today = 0
    for p in latest_files(__import__('config').LOGS, 80, "*.log"):
        if datetime.fromtimestamp(p.stat().st_mtime).date() == datetime.now().date():
            preview = file_preview(p, 2500)
            if re.search(r"\b(ERROR|FAIL|failed)\b", preview, re.I):
                failures_today += 1

    # Status Cards - Row 1
    st.markdown("### 🎯 Service Status")
    cols = st.columns(4)

    with cols[0]:
        card("Local AI", "Ready" if status["ollama"] else "Offline",
             "Ollama API", "ready" if status["ollama"] else "danger", "🤖")
    with cols[1]:
        has_model = "qwen2.5-coder:14b" in status.get("models", "")
        card("Default Model", "Available" if has_model else "Missing",
             "qwen2.5-coder:14b", "ready" if has_model else "warn", "🧠")
    with cols[2]:
        gpu = "GPU" in status.get("ps", "")
        card("GPU", "Active" if gpu else "CPU", "Acceleration",
             "ready" if gpu else "info", "🎮")
    with cols[3]:
        card("Proxy", "Online" if status["proxy"] else "Offline",
             "free-claude-code", "ready" if status["proxy"] else "warn", "🔗")

    # Status Cards - Row 2
    cols = st.columns(4)
    with cols[0]:
        card("Dashboard", "Online", "http://localhost:8501", "ready", "📊")
    with cols[1]:
        card("GitHub", "Connected" if status["github"] else "Not Connected",
             "CLI auth", "ready" if status["github"] else "warn", "🐙")
    with cols[2]:
        card("Scheduler", "Enabled" if status["scheduled"] else "Disabled",
             "Local only", "warn" if status["scheduled"] else "muted", "⏰")
    with cols[3]:
        card("Projects", str(len(repos)), "Repositories", "info", "📁")

    # Activity
    st.markdown("### 📈 Activity")
    runs = today_count(__import__('config').LOGS, "web-ai-*.log")
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