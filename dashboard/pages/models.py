"""
Models Page
===========
Model selection with visual cards and easy switching.
"""
import streamlit as st

from dashboard.data.routing import recommend_execution_plan
from dashboard.data.keys import key_present
from dashboard.data.profiles import load_profiles
from dashboard.data.settings import load_settings, save_settings
from dashboard.services import (
    describe_service_status_snapshot,
    ensure_service_status_snapshot_fresh,
    get_service_status,
    get_service_status_snapshot,
)
from dashboard.ui.components import section_header, card, action_result, chip, info_panel
from dashboard.utils import run_ps


def render():
    """Render models page."""
    section_header(
        "Models",
        "Select and manage AI models",
        [("Free Local", "ready"), ("GPU Accelerated", "info")]
    )

    settings = load_settings()
    status = get_service_status_snapshot(include_optional=True, include_model_details=True)
    ensure_service_status_snapshot_fresh(include_optional=True, include_model_details=True)
    routing_preview = recommend_execution_plan(
        "deep_planning",
        active_projects=2,
        status=status,
        allow_paid=bool(settings.get("autoRouting", True)),
    )

    # Status overview
    st.markdown("### 📊 System Status")
    cols = st.columns(3)

    with cols[0]:
        card("Ollama", "Online" if status["ollama"] else "Offline",
             "Local server", "ready" if status["ollama"] else "danger")
    with cols[1]:
        has_default = "qwen2.5-coder:14b" in status.get("models", "")
        card("Default Model", "Available" if has_default else "Missing",
             "qwen2.5-coder:14b", "ready" if has_default else "warn")
    with cols[2]:
        gpu_active = "GPU" in status.get("ps", "")
        card("GPU", "Active" if gpu_active else "CPU Only",
             "Acceleration", "ready" if gpu_active else "info")

    info_panel(
        "Automatic Routing",
        f"With auto routing {'enabled' if settings.get('autoRouting', True) else 'disabled'}, the dashboard currently recommends `{routing_preview['chosen_model']}` for deeper planning or multi-project work.",
        "info",
    )
    st.caption(describe_service_status_snapshot(status))

    if st.button("↻ Refresh runtime details", use_container_width=True):
        get_service_status(force_refresh=True, include_optional=True, include_model_details=True)
        st.rerun()

    # Model Selector
    st.markdown("### 🎯 Model Selector")
    st.info("Select your default model. Green = ready, Yellow = needs setup. Runtime details are loaded from the last refresh so this page opens instantly.")

    profiles = load_profiles()
    if not profiles:
        st.error("No model profiles were loaded. Check `configs/model-profiles.json`.")
        return

    current_model = settings.get("defaultModel", "ollama/qwen2.5-coder:14b")

    for profile_name, profile in profiles.items():
        if profile_name == "fallback":
            continue

        is_paid = profile.get("paid", False)
        model_id = f"{profile.get('provider')}/{profile.get('model')}"
        is_selected = current_model == model_id

        # Determine status
        if is_paid:
            key_ok = key_present(profile.get("apiKeyEnvVar"))
            status_color = "ready" if key_ok else "warn"
            status_text = "✅ Key ready" if key_ok else "⚠️ Key missing"
        else:
            models_list = status.get("models", "")
            model_short = profile.get("model", "").split(":")[0]
            is_available = model_short in models_list or profile.get("model") in models_list
            status_color = "ready" if is_available else "warn"
            status_text = "✅ Available" if is_available else "⚠️ Not downloaded"

        # Model row
        with st.container():
            cols = st.columns([4, 2, 1])

            with cols[0]:
                icon = "💳" if is_paid else "🆓"
                provider = profile.get("provider", "unknown").title()
                st.markdown(f"**{icon} {provider}** - `{profile.get('model')}`")
                st.caption(f"_{profile.get('role', '')}_")

            with cols[1]:
                st.markdown(chip(status_text, status_color), unsafe_allow_html=True)

            with cols[2]:
                if is_selected:
                    st.button("✓ Selected", disabled=True, key=f"sel_{profile_name}")
                else:
                    if st.button("Select", key=f"sel_{profile_name}"):
                        new_settings = settings.copy()
                        new_settings["defaultModel"] = model_id
                        save_settings(new_settings)
                        st.success(f"✅ Default model set to {model_id}")
                        st.rerun()

        st.divider()

    # Model info
    st.markdown("### 📦 Installed Models")
    col1, col2 = st.columns(2)
    with col1:
        st.code(status.get("models", "No models"), language="text")
    with col2:
        st.code(status.get("ps", "No running models"), language="text")

    # Actions
    st.markdown("### 🔧 Actions")
    cols = st.columns(5)
    actions = [
        ("🚀 Start Stack", "start-local-model-stack.ps1"),
        ("🔍 Health", "health-local-ai-stack.ps1"),
        ("🧪 Test", "test-local-model.ps1"),
        ("🔗 Proxy", "start-free-claude-code-proxy.ps1"),
    ]

    for i, (label, script) in enumerate(actions):
        with cols[i]:
            if st.button(label, key=f"act_{i}"):
                code, out = run_ps(script, timeout=300)
                action_result(label, code, out)
