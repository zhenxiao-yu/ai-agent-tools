"""
Settings Page
=============
Dashboard settings and configuration.
"""
import streamlit as st

from dashboard.data.allowlist import read_allowlist, write_allowlist, validate_repo
from dashboard.data.profiles import get_profile_choices
from dashboard.data.settings import load_settings, save_settings
from dashboard.ui.components import section_header
from dashboard.utils import normalize_repo_path, ps_inline, run_cmd, validate_branch_name


def render():
    """Render settings page."""
    settings = load_settings()

    section_header(
        "Settings",
        "Configure dashboard defaults",
        [("Safety Mode", "ready" if settings.get("safetyMode") else "warn")]
    )

    # Settings form
    st.markdown("### General Settings")

    col1, col2 = st.columns(2)

    with col1:
        # Model selector
        model_options = get_profile_choices()
        if not model_options:
            st.error("No valid model profiles are available. Check `configs/model-profiles.json`.")
            return
        current_model = settings.get("defaultModel", "ollama/qwen2.5-coder:14b")

        # Find current index
        default_index = 0
        for i, (_, model_id, _) in enumerate(model_options):
            if model_id == current_model:
                default_index = i
                break

        selected_idx = st.selectbox(
            "Default Model",
            range(len(model_options)),
            index=default_index,
            format_func=lambda i: model_options[i][0],
            help="Select the default AI model for operations"
        )
        new_model = model_options[selected_idx][1]

        # Branch
        new_branch = st.text_input(
            "Default Branch",
            value=settings.get("defaultBaseBranch", "main"),
            help="Default base branch for AI operations"
        )

    with col2:
        # Interval
        interval_options = [1, 2, 4, 8]
        current_interval = settings.get("defaultIntervalHours", 2)
        interval_index = interval_options.index(current_interval) if current_interval in interval_options else 1

        new_interval = st.selectbox(
            "Check Interval (Hours)",
            interval_options,
            index=interval_index,
            help="Default interval for scheduled checks"
        )

        # Toggles
        new_safety = st.toggle(
            "Safety Mode",
            value=bool(settings.get("safetyMode", True)),
            help="Require confirmation for risky actions"
        )

        new_auto_routing = st.toggle(
            "Auto Routing",
            value=bool(settings.get("autoRouting", True)),
            help="Let the dashboard recommend the best model and lane strategy for different task types."
        )

    # Save button
    if st.button("Save Settings", type="primary", use_container_width=True):
        branch_ok, branch_error = validate_branch_name(new_branch)
        if not branch_ok:
            st.error(branch_error)
            return
        new_settings = {
            "defaultModel": new_model,
            "defaultBaseBranch": new_branch.strip(),
            "defaultIntervalHours": new_interval,
            "safetyMode": new_safety,
            "autoRouting": new_auto_routing,
        }
        save_settings(new_settings)
        st.success("Settings saved.")
        st.rerun()

    # Allowlist editor
    st.markdown("---")
    st.markdown("### Repository Allowlist")

    current_repos = read_allowlist()

    # Add new repo
    with st.expander("Add Repository", expanded=len(current_repos) == 0):
        new_path = st.text_input(
            "Repository Path",
            placeholder=r"C:\path\to\repo",
            help="Full path to a Git repository with a supported project file such as package.json or pyproject.toml"
        )

        if st.button("Validate and Add"):
            normalized_path = normalize_repo_path(new_path)
            valid, msg = validate_repo(normalized_path)
            if valid:
                if normalized_path not in current_repos:
                    current_repos.append(normalized_path)
                    write_allowlist(current_repos)
                    st.success(f"Added: {normalized_path}")
                    st.rerun()
                else:
                    st.info("Repository already in list")
            else:
                st.error(msg)

    # Current repos
    if current_repos:
        st.markdown("**Current repositories:**")
        for i, repo in enumerate(current_repos):
            cols = st.columns([5, 1, 1, 1])
            with cols[0]:
                st.code(repo)
            with cols[1]:
                if st.button("Explorer", key=f"explorer_repo_{i}", help="Open this folder in File Explorer"):
                    safe = repo.replace("'", "''")
                    code, out = ps_inline(f"Start-Process explorer.exe -ArgumentList '{safe}'", timeout=10)
                    if code != 0:
                        st.error(f"Could not open Explorer: {out}")
            with cols[2]:
                if st.button("VS Code", key=f"code_repo_{i}", help="Open this repo in VS Code"):
                    code, out = run_cmd(["code", repo], timeout=15)
                    if code != 0:
                        st.error("VS Code launch failed. Make sure 'code' is on PATH.")
            with cols[3]:
                if st.button("Remove", key=f"del_repo_{i}"):
                    current_repos.pop(i)
                    write_allowlist(current_repos)
                    st.rerun()
    else:
        st.info("No repositories configured. Add one above.")

    st.warning("Never store API keys here. Use the Providers page.")
