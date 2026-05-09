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
from dashboard.ui.components import action_result, card_grid, chip, info_panel, section_header, status_rows
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
    st.markdown("### System Status")
    has_default = "qwen2.5-coder:14b" in status.get("models", "")
    gpu_active = "GPU" in status.get("ps", "")
    status_rows([
        ("Runtime", "Online" if status["ollama"] else "Offline", "ready" if status["ollama"] else "danger"),
        ("Default Model", "Ready" if has_default else "Needs Setup", "ready" if has_default else "warn"),
        ("Compute", "Active" if gpu_active else "Unknown", "ready" if gpu_active else "info"),
    ])
    card_grid([
        {
            "title": "Ollama",
            "value": "Online" if status["ollama"] else "Offline",
            "detail": "Local runtime",
            "tone": "ready" if status["ollama"] else "danger",
        },
        {
            "title": "Default Model",
            "value": "Available" if has_default else "Needs Setup",
            "detail": "Default local coding model",
            "tone": "ready" if has_default else "warn",
        },
        {
            "title": "Compute",
            "value": "Active" if gpu_active else "CPU Only",
            "detail": "Acceleration",
            "tone": "ready" if gpu_active else "info",
        },
    ])

    info_panel(
        "Automatic Routing",
        f"With auto routing {'enabled' if settings.get('autoRouting', True) else 'disabled'}, the dashboard currently recommends {routing_preview['chosen_model']} for deeper planning or multi-project work.",
        "info",
    )
    st.caption(describe_service_status_snapshot(status))

    if st.button("Refresh Runtime Details", use_container_width=True):
        get_service_status(force_refresh=True, include_optional=True, include_model_details=True)
        st.rerun()

    # Model Selector
    st.markdown("### Model Selector")
    st.info("Select the default model. Ready models are available now. Runtime details are loaded from the last refresh so this page opens instantly.")

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
            status_text = "Key Ready" if key_ok else "Key Missing"
        else:
            models_list = status.get("models", "")
            model_short = profile.get("model", "").split(":")[0]
            is_available = model_short in models_list or profile.get("model") in models_list
            status_color = "ready" if is_available else "warn"
            status_text = "Available" if is_available else "Not Downloaded"

        # Model row
        with st.container():
            cols = st.columns([4, 2, 1])

            with cols[0]:
                provider = profile.get("provider", "unknown").title()
                st.markdown(f"**{provider}**")
                st.caption(profile.get("model", "unknown"))
                st.caption(f"_{profile.get('role', '')}_")

            with cols[1]:
                st.markdown(chip(status_text, status_color), unsafe_allow_html=True)

            with cols[2]:
                if is_selected:
                    st.button("Selected", disabled=True, key=f"sel_{profile_name}")
                else:
                    if st.button("Select", key=f"sel_{profile_name}"):
                        new_settings = settings.copy()
                        new_settings["defaultModel"] = model_id
                        save_settings(new_settings)
                        st.success(f"Default model set to {model_id}")
                        st.rerun()

        st.divider()

    # Recommended pulls — one-click installs of the curated coding model set.
    st.markdown("### Recommended Coding Models")
    installed_text = status.get("models", "") or ""
    recommended = [
        ("qwen2.5-coder:7b", "Fast coder (~5 GB)", "Lower-VRAM coder. Best for laptops or background runs."),
        ("qwen2.5-coder:14b", "Default coder (~9 GB)", "Sweet spot for desktop GPUs. Used by the worker by default."),
        ("llama3.1:8b", "Planner / chat (~5 GB)", "Better long-context reasoning for the pipeline's planning roles."),
    ]
    rec_cols = st.columns(3)
    for i, (tag, label, blurb) in enumerate(recommended):
        with rec_cols[i]:
            already = tag in installed_text
            st.markdown(f"**{label}**")
            st.caption(f"`{tag}`")
            st.caption(blurb)
            if already:
                st.button("Installed", key=f"pull_{i}", disabled=True, use_container_width=True)
            else:
                if st.button(f"Pull {tag.split(':')[0]}", key=f"pull_{i}", use_container_width=True):
                    code, out = run_ps("tune-ollama.ps1", "-ModelsToPull", tag, timeout=3600)
                    action_result(f"Pull {tag}", code, out)

    # Model info
    with st.expander("Advanced Runtime Output"):
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Installed models")
            st.code(status.get("models", "No models"), language="text")
        with col2:
            st.caption("Running models")
            st.code(status.get("ps", "No running models"), language="text")

    # Actions
    st.markdown("### Actions")

    st.caption("Local stack")
    stack_cols = st.columns(4)
    stack_actions = [
        ("Start Stack", "start-local-model-stack.ps1"),
        ("Stop Stack", "stop-local-model-stack.ps1"),
        ("Health", "health-local-ai-stack.ps1"),
        ("Test", "test-local-model.ps1"),
    ]
    for i, (label, script) in enumerate(stack_actions):
        with stack_cols[i]:
            if st.button(label, key=f"stack_act_{i}", use_container_width=True):
                code, out = run_ps(script, timeout=300)
                action_result(label, code, out)

    st.caption("Ollama tuning")
    tune_cols = st.columns(3)
    with tune_cols[0]:
        if st.button(
            "Tune Ollama",
            key="tune_ollama",
            use_container_width=True,
            help="Persist sane defaults: OLLAMA_KEEP_ALIVE=30m, NUM_PARALLEL=2, MAX_LOADED_MODELS=2.",
        ):
            code, out = run_ps("tune-ollama.ps1", timeout=120)
            action_result("Tune Ollama", code, out)
    with tune_cols[1]:
        if st.button(
            "Pull Recommended",
            key="tune_pull",
            use_container_width=True,
            help="Download the curated coding-model set (qwen2.5-coder + llama3.1).",
        ):
            code, out = run_ps("tune-ollama.ps1", "-InstallRecommended", timeout=3600)
            action_result("Pull Recommended Models", code, out)
    with tune_cols[2]:
        if st.button(
            "Reset Tuning",
            key="tune_reset",
            use_container_width=True,
            help="Remove the persisted Ollama env vars.",
        ):
            code, out = run_ps("tune-ollama.ps1", "-Reset", timeout=60)
            action_result("Reset Tuning", code, out)

    st.caption("Claude-compatible proxy")
    proxy_cols = st.columns(4)
    proxy_running = bool(status.get("proxy"))
    proxy_actions = [
        ("Start Proxy", "start-free-claude-code-proxy.ps1", []),
        ("Stop Proxy", "stop-free-claude-code-proxy.ps1", []),
        ("Restart Proxy", None, None),  # composite
        ("Test Proxy", "test-free-claude-code-proxy.ps1", []),
    ]
    for i, (label, script, extra) in enumerate(proxy_actions):
        with proxy_cols[i]:
            disabled = (label == "Stop Proxy" and not proxy_running) or (
                label == "Test Proxy" and not proxy_running
            )
            if st.button(label, key=f"proxy_act_{i}", disabled=disabled, use_container_width=True):
                if label == "Restart Proxy":
                    code1, out1 = run_ps("stop-free-claude-code-proxy.ps1", timeout=60)
                    code2, out2 = run_ps("start-free-claude-code-proxy.ps1", timeout=300)
                    code = code1 if code1 != 0 else code2
                    out = "[stop]\n" + (out1 or "") + "\n[start]\n" + (out2 or "")
                else:
                    code, out = run_ps(script, *(extra or []), timeout=300)
                action_result(label, code, out)
                if label in ("Start Proxy", "Stop Proxy", "Restart Proxy"):
                    get_service_status(force_refresh=True, include_optional=True, include_model_details=True)
                    st.rerun()
