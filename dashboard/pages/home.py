"""
Home Page
=========
Dashboard home with service status and quick actions.
"""
from datetime import datetime
from pathlib import Path
import re

import streamlit as st

from dashboard import jobs as jobs_mod
from dashboard.cache import invalidate_cache
from dashboard.config import LOGS
from dashboard.data.allowlist import read_allowlist
from dashboard.data.routing import recommend_execution_plan
from dashboard.data.settings import load_settings
from dashboard.services import (
    describe_service_status_snapshot,
    ensure_service_status_snapshot_fresh,
    get_service_status,
    get_service_status_snapshot,
)
from dashboard.ui.components import (
    card_grid,
    info_panel,
    quick_action,
    section_header,
    status_rows,
)
from dashboard.utils import latest_files, file_preview, today_count, recent_dashboard_events


def _submit(kind: str, label: str, script: str, args: list[str], repo: str = "") -> None:
    job = jobs_mod.submit(kind=kind, label=label, script=script, args=args, repo=repo)
    st.success(f"{label} submitted as {job.id}. Open the Runs page to follow it.")


def render():
    """Render home page."""
    section_header(
        "Dashboard",
        "System overview and quick actions",
        [("Free Local", "ready"), ("Stable", "info")]
    )

    # Quick Actions
    st.markdown("### Quick Actions")
    actions = [
        ("Start Stack", "start-local-model-stack.ps1", "Start the local AI stack"),
        ("Stop Stack", "stop-local-model-stack.ps1", "Stop Ollama and the local stack"),
        ("Health Check", "doctor-local-ai.ps1", "Run machine diagnostics"),
        ("Morning Review", "morning-review.ps1", "Show AI branches, diffs, and the latest reports"),
        ("Open VS Code", "open-ai-tools-vscode.ps1", "Open the workspace"),
        ("Monitor", "ai-stack-monitor.ps1", "Review local resource usage"),
    ]

    for row_start in range(0, len(actions), 3):
        cols = st.columns(3)
        for col_index, (label, script, help_text) in enumerate(actions[row_start:row_start + 3]):
            with cols[col_index]:
                quick_action(label, script, help_text=help_text)
    if st.button("Refresh Dashboard", help="Refresh cached service and settings state", use_container_width=True):
        invalidate_cache()
        get_service_status(force_refresh=True)
        st.rerun()

    # Run worker / reviewer on a configured repo
    repos = read_allowlist()
    settings_data = load_settings()
    st.markdown("### Run on a Project")
    if not repos:
        st.info("Add a repo on the Settings page to enable Run Worker, Dry Run, and Run Reviewer here.")
    else:
        run_cols = st.columns([3, 2])
        with run_cols[0]:
            target_repo = st.selectbox(
                "Repository",
                repos,
                key="home_run_repo",
                help="Choose any repository in your allowlist.",
            )
        with run_cols[1]:
            base_branch = st.text_input(
                "Base branch",
                value=settings_data.get("defaultBaseBranch", "main"),
                key="home_run_branch",
                help="Worker will branch off this and refuse a dirty repo.",
            )

        worker_cmd = (
            f'powershell -ExecutionPolicy Bypass -File scripts\\run-web-ai-worker.ps1 '
            f'-RepoPath "{target_repo}" -BaseBranch "{base_branch}"'
        )
        reviewer_cmd = (
            f'powershell -ExecutionPolicy Bypass -File scripts\\run-ai-reviewer.ps1 '
            f'-RepoPath "{target_repo}"'
        )
        with st.expander("Show exact commands", expanded=False):
            st.caption("These are the commands the buttons below will run.")
            st.code(worker_cmd + " -DryRun", language="powershell")
            st.code(worker_cmd, language="powershell")
            st.code(reviewer_cmd, language="powershell")

        action_cols = st.columns(4)
        with action_cols[0]:
            if st.button("Dry Run Worker", use_container_width=True, help="Verify env, no edits, no commits. Runs in the background."):
                _submit(
                    kind="dry-run",
                    label=f"Dry Run · {Path(target_repo).name}",
                    script="run-web-ai-worker.ps1",
                    args=["-RepoPath", target_repo, "-BaseBranch", base_branch, "-DryRun"],
                    repo=target_repo,
                )
        with action_cols[1]:
            if st.button(
                "Run Worker",
                use_container_width=True,
                help="One-task local worker on a fresh ai/web-auto-* branch. No commits, no pushes.",
            ):
                _submit(
                    kind="worker",
                    label=f"Worker · {Path(target_repo).name}",
                    script="run-web-ai-worker.ps1",
                    args=["-RepoPath", target_repo, "-BaseBranch", base_branch],
                    repo=target_repo,
                )
        with action_cols[2]:
            if st.button(
                "Run Reviewer",
                use_container_width=True,
                help="Have the local model review the current diff in the chosen repo.",
            ):
                _submit(
                    kind="reviewer",
                    label=f"Reviewer · {Path(target_repo).name}",
                    script="run-ai-reviewer.ps1",
                    args=["-RepoPath", target_repo],
                    repo=target_repo,
                )
        with action_cols[3]:
            if st.button(
                "Run Pipeline",
                use_container_width=True,
                help="Run the full PM → Tech Lead → QA → Reviewer → DevOps advisory chain. No edits.",
            ):
                _submit(
                    kind="pipeline",
                    label=f"Pipeline · {Path(target_repo).name}",
                    script="run-agent-pipeline.ps1",
                    args=["-RepoPath", target_repo],
                    repo=target_repo,
                )
        st.caption("Submitted jobs run in the background. Track them on the Runs page; final reports land on Reports.")

    # Service Status
    status = get_service_status_snapshot(include_model_details=False)
    ensure_service_status_snapshot_fresh(include_model_details=False)
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
        st.warning("Attention Needed\n\n- " + "\n- ".join(warnings))

    # Status Cards - Row 1
    st.markdown("### Service Status")
    has_model = "qwen2.5-coder:14b" in status.get("models", "")
    gpu = "GPU" in status.get("ps", "")
    status_rows([
        ("Freshness", describe_service_status_snapshot(status), "info" if status.get("snapshot_ready") else "muted"),
        ("Local Runtime", "Ready" if status.get("snapshot_ready") and status["ollama"] else "Checking" if not status.get("snapshot_ready") else "Offline", "ready" if status.get("snapshot_ready") and status["ollama"] else "info" if not status.get("snapshot_ready") else "danger"),
        ("Repository Setup", f"{len(repos)} configured", "ready" if repos else "warn"),
    ])
    card_grid([
        {
            "title": "Local AI",
            "value": "Ready" if status.get("snapshot_ready") and status["ollama"] else "Checking" if not status.get("snapshot_ready") else "Offline",
            "detail": "Local runtime is reachable" if status.get("snapshot_ready") and status["ollama"] else "Refreshing machine status" if not status.get("snapshot_ready") else "Start the local stack to run agents",
            "tone": "ready" if status.get("snapshot_ready") and status["ollama"] else "info" if not status.get("snapshot_ready") else "danger",
        },
        {
            "title": "Default Model",
            "value": "Pending" if not status.get("snapshot_ready") else "Review Models" if status["ollama"] and not status.get("models") else "Available" if has_model else "Needs Setup",
            "detail": "Waiting for runtime snapshot" if not status.get("snapshot_ready") else "Runtime details load on the Models page" if status["ollama"] and not status.get("models") else "Default local coding model",
            "tone": "info" if not status.get("snapshot_ready") or (status["ollama"] and not status.get("models")) else "ready" if has_model else "warn",
        },
        {
            "title": "Compute",
            "value": "Pending" if not status.get("snapshot_ready") else "Active" if gpu else "Unknown",
            "detail": "Waiting for runtime snapshot" if not status.get("snapshot_ready") else "Open Models for live runtime details",
            "tone": "info" if not status.get("snapshot_ready") or not gpu else "ready",
        },
        {
            "title": "Proxy",
            "value": "Checking" if not status.get("snapshot_ready") else "Online" if status["proxy"] else "Offline",
            "detail": "Background snapshot warming up" if not status.get("snapshot_ready") else "Local compatibility endpoint",
            "tone": "info" if not status.get("snapshot_ready") else "ready" if status["proxy"] else "warn",
        },
    ])

    # Status Cards - Row 2
    card_grid([
        {"title": "Dashboard", "value": "Online", "detail": "Control center is running", "tone": "ready"},
        {
            "title": "GitHub",
            "value": "Checking" if not status.get("snapshot_ready") else "Connected" if status["github"] else "Not Connected",
            "detail": "Background snapshot warming up" if not status.get("snapshot_ready") else "Repository operations available" if status["github"] else "Sign in to enable repository operations",
            "tone": "info" if not status.get("snapshot_ready") else "ready" if status["github"] else "warn",
        },
        {
            "title": "Scheduler",
            "value": "Checking" if not status.get("snapshot_ready") else "Enabled" if status["scheduled"] else "Disabled",
            "detail": "Background snapshot warming up" if not status.get("snapshot_ready") else "Local recurring checks" if status["scheduled"] else "Manual runs only",
            "tone": "info" if not status.get("snapshot_ready") else "warn" if status["scheduled"] else "muted",
        },
        {"title": "Projects", "value": str(len(repos)), "detail": "Repositories", "tone": "info"},
    ])

    st.markdown("### Plug-and-Play Workflow")
    cols = st.columns(3)
    with cols[0]:
        info_panel("1. Pick a Lane", "Home stays fast. Use Automation to preview routing and Models only when you need deeper runtime details.", "info")
    with cols[1]:
        info_panel("2. Let It Queue", f"Recommended route uses {plan['chosen_model']} with {plan['lane_mode'].lower()}.", "ready")
    with cols[2]:
        info_panel("3. Review Outputs", "Workers should surface logs, validation, and reports as results of a run, not hidden side effects.", "ready")

    # Activity
    st.markdown("### Activity")
    runs = today_count(LOGS, "web-ai-*.log")
    card_grid([
        {"title": "Runs Today", "value": str(runs), "detail": "Worker executions", "tone": "info"},
        {
            "title": "Failures",
            "value": str(failures_today),
            "detail": "Errors detected today",
            "tone": "danger" if failures_today else "ready",
        },
    ])
    activity_cols = st.columns(2)
    with activity_cols[0]:
        if st.button("Open Reports", use_container_width=True, help="See worker, reviewer, and doctor outputs"):
            st.session_state["nav_page"] = "Reports"
            st.session_state["current_page"] = "Reports"
            st.rerun()
    with activity_cols[1]:
        if st.button(
            "Investigate Failures",
            use_container_width=True,
            disabled=failures_today == 0,
            help="Jump to Reports and pre-filter for errors",
        ):
            st.session_state["nav_page"] = "Reports"
            st.session_state["current_page"] = "Reports"
            st.session_state["reports_focus_path"] = None
            st.rerun()

    st.markdown("### Next Steps")
    if not repos:
        st.info("Add your first project.\n\nUse the Settings page to register a repo path.")
    elif failures_today > 0:
        st.warning("Some logs reported errors today. Open Reports to triage.")
    else:
        st.success("All systems are ready. Run a dry-run on any project to start.")

    st.markdown("### Multi-Project Impact")
    card_grid([
        {"title": "Routing Advice", "value": plan["route_label"], "detail": plan["reason"], "tone": "info"},
        {
            "title": "Parallel Lanes",
            "value": str(plan["recommended_concurrency"]),
            "detail": plan["lane_mode"],
            "tone": "warn" if plan["recommended_concurrency"] > 1 else "ready",
        },
        {
            "title": "Speed Impact",
            "value": "Queue Grows" if len(repos) > 1 else "Stable",
            "detail": plan["speed_note"],
            "tone": "warn" if len(repos) > 1 else "ready",
        },
    ])

    with st.expander("Diagnostics and Recent Dashboard Logs"):
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
