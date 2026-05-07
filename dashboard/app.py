"""
Local AI Mission Control
========================
Refactored dashboard with modular architecture.
"""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from dashboard.config import PAGE_ICONS
from dashboard.data.settings import load_settings
from dashboard.data.routing import recommend_execution_plan
from dashboard.services import get_service_status, get_service_status_snapshot
from dashboard.ui.styles import render_styles
from dashboard.ui.components import chip, error_boundary, info_panel
from dashboard.utils import log_event

# Import page modules
from dashboard.pages import home, providers, models, settings, automation


# Page registry
PAGES = {
    "Home": home,
    "Automation": automation,
    "Providers": providers,
    "Models": models,
    "Settings": settings,
}


def render_navigation() -> str:
    """Render top navigation and return the selected page."""
    pages = list(PAGES.keys())
    if "current_page" not in st.session_state or st.session_state["current_page"] not in pages:
        st.session_state["current_page"] = "Home"

    st.markdown('<div class="top-nav-wrap"><div class="top-nav-title">Workspace Navigation</div>', unsafe_allow_html=True)
    selected = st.radio(
        "Navigate",
        pages,
        key="current_page",
        horizontal=True,
        label_visibility="collapsed",
        format_func=lambda page: f"{PAGE_ICONS.get(page, '📄')} {page}",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return selected


def render_sidebar():
    """Render contextual dock rather than primary navigation."""
    with st.sidebar:
        st.markdown('<div class="dock-panel"><div class="dock-title">Control Dock</div>', unsafe_allow_html=True)

        # Quick status
        status = get_service_status_snapshot()
        plan = recommend_execution_plan(
            task_key="parallel_projects",
            active_projects=2,
            status=status,
            allow_paid=bool(load_settings().get("autoRouting", True)),
        )

        status_items = [
            ("🟢" if status["ollama"] else "🔴", "Ollama", status["ollama"]),
            ("🟢" if status["proxy"] else "🔴", "Proxy", status["proxy"]),
            ("🟢" if status["github"] else "🟡", "GitHub", status["github"]),
        ]

        for icon, name, is_ok in status_items:
            status_text = "Online" if is_ok else "Offline"
            st.markdown(f"{icon} **{name}**: {status_text}")

        if status.get("errors"):
            st.caption(f"{len(status['errors'])} background checks degraded")
        st.caption("Showing last known status for instant navigation.")

        if st.button("↻ Refresh Dock Status", use_container_width=True):
            get_service_status(force_refresh=True)
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Safety mode indicator
        settings_data = load_settings()
        safety = settings_data.get("safetyMode", True)
        info_panel(
            "Runtime Mode",
            f"{'Safety mode is on and confirmations stay explicit.' if safety else 'Safety mode is off, so review each action carefully.'}",
            "ready" if safety else "warn",
        )

        # Current model
        current_model = settings_data.get("defaultModel", "ollama/qwen2.5-coder:14b")
        info_panel(
            "Current Model",
            f"Default: `{current_model}`\n\nAuto route suggests `{plan['chosen_model']}` when work fans out.",
            "info",
        )

        if st.button("🔄 Switch Model"):
            st.session_state["current_page"] = "Models"
            st.rerun()
        if st.button("🧠 Open Automation"):
            st.session_state["current_page"] = "Automation"
            st.rerun()


def render_header():
    """Render page header."""
    st.markdown("""
    <div class="hero animate-in">
        <h1>🚀 Local AI Mission Control</h1>
        <p>Free local coding agents with safety gates and intelligent orchestration</p>
    </div>
    <div class="top-banner animate-in">
        🛡️ Free Local by default · Paid providers manual-only · No auto-push · No auto-commit
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Local AI Mission Control",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Render styles
    render_styles()

    # Render header
    render_header()

    # Render top navigation
    current_page = render_navigation()

    # Render contextual dock
    render_sidebar()

    # Render selected page with error handling
    page_module = PAGES.get(current_page)
    if page_module and hasattr(page_module, "render"):
        error_boundary(
            f"{current_page} page",
            page_module.render,
            help_text="This page hit a recoverable error. Diagnostics have been logged.",
        )
    else:
        st.error(f"Page '{current_page}' not found")
        log_event("page_missing", "Unknown page requested", {"page": current_page})


if __name__ == "__main__":
    main()
