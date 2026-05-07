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

from dashboard.data.settings import load_settings
from dashboard.data.routing import recommend_execution_plan
from dashboard.services import (
    describe_service_status_snapshot,
    ensure_service_status_snapshot_fresh,
    get_service_status,
    get_service_status_snapshot,
)
from dashboard.ui.styles import render_styles
from dashboard.ui.components import error_boundary, info_panel
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


def navigate_to(page: str) -> None:
    """Synchronize widget state and current page selection."""
    if page in PAGES:
        st.session_state["current_page"] = page
        st.session_state["nav_page"] = page


def render_navigation() -> str:
    """Render top navigation and return the selected page."""
    pages = list(PAGES.keys())
    if "current_page" not in st.session_state or st.session_state["current_page"] not in pages:
        st.session_state["current_page"] = "Home"
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in pages:
        st.session_state["nav_page"] = st.session_state["current_page"]

    st.markdown('<div class="top-nav-wrap"><div class="top-nav-title">Workspace Navigation</div>', unsafe_allow_html=True)
    selected = st.radio(
        "Navigate",
        pages,
        key="nav_page",
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state["current_page"] = selected
    return selected


def render_sidebar():
    """Render contextual dock rather than primary navigation."""
    with st.sidebar:
        st.markdown('<div class="dock-panel"><div class="dock-title">Control Dock</div>', unsafe_allow_html=True)

        # Quick status
        status = get_service_status_snapshot()
        ensure_service_status_snapshot_fresh()
        plan = recommend_execution_plan(
            task_key="parallel_projects",
            active_projects=2,
            status=status,
            allow_paid=bool(load_settings().get("autoRouting", True)),
        )

        if status.get("snapshot_ready"):
            status_items = [
                ("Online" if status["ollama"] else "Offline", "Ollama"),
                ("Online" if status["proxy"] else "Offline", "Proxy"),
                ("Connected" if status["github"] else "Limited", "GitHub"),
            ]

            for status_text, name in status_items:
                st.markdown(f"**{name}**")
                st.caption(status_text)

            if status.get("errors"):
                st.caption(f"{len(status['errors'])} background checks degraded")
        else:
            st.markdown("**Machine Status**")
            st.caption("Warming up")
            st.markdown("**Routing Signals**")
            st.caption("Loading snapshot")

        st.caption(describe_service_status_snapshot(status))
        st.caption("Instant navigation uses saved status, not live probes.")

        if st.button("Refresh Status", use_container_width=True):
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
            f"Default: {current_model}\n\nAuto route suggests {plan['chosen_model']} when work fans out.",
            "info",
        )

        st.markdown('<div class="dock-panel"><div class="dock-title">Shortcuts</div>', unsafe_allow_html=True)
        shortcut_cols = st.columns(2)
        with shortcut_cols[0]:
            st.button("Automation", use_container_width=True, on_click=navigate_to, args=("Automation",))
            st.button("Providers", use_container_width=True, on_click=navigate_to, args=("Providers",))
        with shortcut_cols[1]:
            st.button("Models", use_container_width=True, on_click=navigate_to, args=("Models",))
            st.button("Settings", use_container_width=True, on_click=navigate_to, args=("Settings",))
        st.markdown("</div>", unsafe_allow_html=True)


def render_header():
    """Render page header."""
    st.markdown("""
    <div class="hero animate-in">
        <h1>Local AI Mission Control</h1>
        <p>Local-first coding operations with stable routing, clear controls, and faster page transitions.</p>
    </div>
    <div class="top-banner animate-in">
        Local by default. Paid providers stay manual. Pushes and commits remain explicit.
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Local AI Mission Control",
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
