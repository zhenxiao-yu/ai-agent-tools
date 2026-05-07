"""
Settings Page
=============
Dashboard settings and configuration.
"""
import streamlit as st

from cache import invalidate_cache
from config import PAGE_ICONS
from data.allowlist import read_allowlist, write_allowlist, validate_repo
from data.profiles import get_profile_choices
from data.settings import load_settings, save_settings
from ui.components import section_header, card


def render():
    """Render settings page."""
    settings = load_settings()

    section_header(
        "Settings",
        "Configure dashboard defaults",
        [("Safety Mode", "ready" if settings.get("safetyMode") else "warn")]
    )

    # Settings form
    st.markdown("### ⚙️ General Settings")

    col1, col2 = st.columns(2)

    with col1:
        # Model selector
        model_options = get_profile_choices()
        current_model = settings.get("defaultModel", "ollama/qwen2.5-coder:14b")

        # Find current index
        default_index = 0
        for i, (_, model_id, _) in enumerate(model_options):
            if model_id == current_model:
                default_index = i
                break

        selected_idx = st.selectbox(
            "🧠 Default Model",
            range(len(model_options)),
            index=default_index,
            format_func=lambda i: model_options[i][0],
            help="Select the default AI model for operations"
        )
        new_model = model_options[selected_idx][1]

        # Branch
        new_branch = st.text_input(
            "🌿 Default Branch",
            value=settings.get("defaultBaseBranch", "main"),
            help="Default base branch for AI operations"
        )

    with col2:
        # Interval
        interval_options = [1, 2, 4, 8]
        current_interval = settings.get("defaultIntervalHours", 2)
        interval_index = interval_options.index(current_interval) if current_interval in interval_options else 1

        new_interval = st.selectbox(
            "⏱️ Check Interval (hours)",
            interval_options,
            index=interval_index,
            help="Default interval for scheduled checks"
        )

        # Toggles
        new_safety = st.toggle(
            "🛡️ Safety Mode",
            value=bool(settings.get("safetyMode", True)),
            help="Require confirmation for risky actions"
        )

        new_advanced = st.toggle(
            "⚡ Advanced Mode",
            value=bool(settings.get("advancedMode", False)),
            help="Show advanced options"
        )

    # Save button
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        new_settings = {
            "defaultModel": new_model,
            "defaultBaseBranch": new_branch,
            "defaultIntervalHours": new_interval,
            "safetyMode": new_safety,
            "advancedMode": new_advanced,
        }
        save_settings(new_settings)
        st.success("✅ Settings saved!")
        st.rerun()

    # Allowlist editor
    st.markdown("---")
    st.markdown("### 📋 Repository Allowlist")

    current_repos = read_allowlist()

    # Add new repo
    with st.expander("➕ Add Repository", expanded=len(current_repos) == 0):
        new_path = st.text_input(
            "Repository Path",
            placeholder=r"C:\path\to\repo",
            help="Full path to a Git repository with a supported project file such as package.json or pyproject.toml"
        )

        if st.button("✅ Validate & Add"):
            valid, msg = validate_repo(new_path)
            if valid:
                if new_path not in current_repos:
                    current_repos.append(new_path)
                    write_allowlist(current_repos)
                    st.success(f"Added: {new_path}")
                    st.rerun()
                else:
                    st.info("Repository already in list")
            else:
                st.error(msg)

    # Current repos
    if current_repos:
        st.markdown("**Current repositories:**")
        for i, repo in enumerate(current_repos):
            cols = st.columns([5, 1])
            with cols[0]:
                st.code(repo)
            with cols[1]:
                if st.button("🗑️", key=f"del_repo_{i}"):
                    current_repos.pop(i)
                    write_allowlist(current_repos)
                    st.rerun()
    else:
        st.info("No repositories configured. Add one above.")

    st.warning("⚠️ Never store API keys here. Use the Providers page.")
