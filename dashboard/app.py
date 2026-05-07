"""
Local AI Mission Control
========================
Refactored dashboard with modular architecture.
"""
import streamlit as st

from config import PAGE_ICONS
from data.settings import load_settings, is_safety_mode
from services import get_service_status
from ui.styles import render_styles
from ui.components import chip

# Import page modules
from pages import home, providers, models, settings


# Page registry
PAGES = {
    "Home": home,
    "Providers": providers,
    "Models": models,
    "Settings": settings,
}


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("### 🧭 Navigation")

        # Page selector
        pages = list(PAGES.keys())
        page_labels = [f"{PAGE_ICONS.get(p, '📄')} {p}" for p in pages]

        selected = st.selectbox(
            "Go to",
            page_labels,
            key="nav_page",
            label_visibility="collapsed"
        )
        current_page = pages[page_labels.index(selected)]

        st.markdown("---")

        # Quick status
        st.markdown("### 📊 Status")
        status = get_service_status()

        status_items = [
            ("🟢" if status["ollama"] else "🔴", "Ollama", status["ollama"]),
            ("🟢" if status["proxy"] else "🔴", "Proxy", status["proxy"]),
            ("🟢" if status["github"] else "🟡", "GitHub", status["github"]),
        ]

        for icon, name, is_ok in status_items:
            status_text = "Online" if is_ok else "Offline"
            st.markdown(f"{icon} **{name}**: {status_text}")

        st.markdown("---")

        # Safety mode indicator
        settings_data = load_settings()
        safety = settings_data.get("safetyMode", True)
        st.markdown(
            chip("Safety Mode ON" if safety else "Safety Mode OFF",
                 "ready" if safety else "warn") + " Confirmation required",
            unsafe_allow_html=True
        )

        # Current model
        st.markdown("---")
        st.markdown("### 🧠 Model")
        current_model = settings_data.get("defaultModel", "ollama/qwen2.5-coder:14b")
        st.code(current_model, language="text")

        if st.button("🔄 Switch Model"):
            st.session_state["nav_page"] = f"{PAGE_ICONS['Models']} Models"
            st.rerun()

    return current_page


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

    # Render sidebar and get current page
    current_page = render_sidebar()

    # Render selected page with error handling
    try:
        page_module = PAGES.get(current_page)
        if page_module and hasattr(page_module, 'render'):
            page_module.render()
        else:
            st.error(f"Page '{current_page}' not found")
    except Exception as e:
        st.error("❌ Page error")
        st.exception(e)
        if st.button("🔄 Reload"):
            st.rerun()


if __name__ == "__main__":
    main()