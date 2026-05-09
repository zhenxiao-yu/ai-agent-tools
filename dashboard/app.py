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
from dashboard.services import (
    describe_service_status_snapshot,
    ensure_service_status_snapshot_fresh,
    get_service_status,
    get_service_status_snapshot,
)
from dashboard.ui.styles import render_styles
from dashboard.ui.components import error_boundary, info_panel, status_rows
from dashboard.utils import log_event

# Import page modules
from dashboard.pages import (
    automation,
    home,
    models,
    providers,
    reports,
    runs,
    scheduler,
    settings,
)


# Page registry
PAGES = {
    "Home": home,
    "Automation": automation,
    "Runs": runs,
    "Reports": reports,
    "Scheduler": scheduler,
    "Providers": providers,
    "Models": models,
    "Settings": settings,
}


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
        st.markdown('<div class="dock-title">Control Dock</div>', unsafe_allow_html=True)

        # Quick status
        status = get_service_status_snapshot()
        ensure_service_status_snapshot_fresh()

        if status.get("snapshot_ready"):
            status_items = [
                ("Ollama", "Online" if status["ollama"] else "Offline", "ready" if status["ollama"] else "danger"),
                ("Proxy", "Online" if status["proxy"] else "Offline", "ready" if status["proxy"] else "warn"),
                ("GitHub", "Connected" if status["github"] else "Limited", "ready" if status["github"] else "warn"),
            ]
            status_rows(status_items)

            if status.get("errors"):
                st.caption(f"{len(status['errors'])} background checks degraded")
        else:
            status_rows([
                ("Machine Status", "Warming Up", "info"),
                ("Routing Signals", "Loading", "muted"),
            ])

        st.caption(describe_service_status_snapshot(status))
        st.caption("Instant navigation uses saved status, not live probes.")

        if st.button("Refresh Status", use_container_width=True):
            get_service_status(force_refresh=True)
            st.rerun()

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
        model_label = current_model.split("/", 1)[-1]
        info_panel(
            "Current Model",
            f"Default local model: {model_label}\n\nAutomation routing is {'enabled' if settings_data.get('autoRouting', True) else 'manual'}.",
            "info",
        )


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
