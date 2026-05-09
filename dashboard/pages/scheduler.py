"""
Scheduler Page
==============
Manage the Windows scheduled task that runs the local web AI worker on a
loop. Wraps install-scheduled-web-worker.ps1 / remove-scheduled-web-worker.ps1
so the user does not have to remember argument names or run elevated terminals
for routine schedule changes.
"""
from __future__ import annotations

import json

import streamlit as st

from dashboard.data.allowlist import read_allowlist
from dashboard.data.settings import load_settings
from dashboard.ui.components import action_result, card_grid, section_header
from dashboard.utils import ps_inline, run_ps


TASK_NAME = "Local Web AI Worker"


def _query_task() -> dict:
    """Return a dict describing the scheduled task, or {} if it does not exist."""
    cmd = (
        f"$t = Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue; "
        "if (-not $t) { '' | Out-Null; exit 0 } "
        "$info = Get-ScheduledTaskInfo -TaskName $t.TaskName; "
        "[pscustomobject]@{"
        " state = $t.State.ToString();"
        " lastRun = if ($info.LastRunTime) { $info.LastRunTime.ToString('o') } else { $null };"
        " nextRun = if ($info.NextRunTime) { $info.NextRunTime.ToString('o') } else { $null };"
        " lastResult = $info.LastTaskResult;"
        " path = $t.TaskPath"
        "} | ConvertTo-Json -Compress"
    )
    code, out = ps_inline(cmd, timeout=15)
    if code != 0 or not out.strip():
        return {}
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {}


def render() -> None:
    """Render scheduler page."""
    section_header(
        "Scheduler",
        "Run one safe worker pass on a loop without leaving the dashboard",
        [("Optional", "warn"), ("Allowlist Required", "info")],
    )

    info = _query_task()
    installed = bool(info)

    summary_cards = [
        {
            "title": "Status",
            "value": "Installed" if installed else "Not Installed",
            "detail": info.get("state", "Use the form below to install"),
            "tone": "ready" if installed else "muted",
        },
        {
            "title": "Last Run",
            "value": (info.get("lastRun") or "—").replace("T", " ").split(".")[0],
            "detail": f"Result: {info.get('lastResult', '—')}" if installed else "No history",
            "tone": "info",
        },
        {
            "title": "Next Run",
            "value": (info.get("nextRun") or "—").replace("T", " ").split(".")[0],
            "detail": "From the Windows Task Scheduler",
            "tone": "info",
        },
    ]
    card_grid(summary_cards)

    settings = load_settings()
    repos = read_allowlist()

    st.markdown("### Install or Update")
    if not repos:
        st.info("Add a repository on the Settings page first. The installer refuses anything that is not on the allowlist.")
        return

    cols = st.columns([3, 1, 1])
    with cols[0]:
        repo = st.selectbox(
            "Repository",
            repos,
            key="scheduler_repo",
            help="The exact path here must already be in configs/repo-allowlist.txt.",
        )
    with cols[1]:
        interval = st.selectbox(
            "Every (hours)",
            [1, 2, 4, 8],
            index=[1, 2, 4, 8].index(settings.get("defaultIntervalHours", 2)),
            key="scheduler_interval",
        )
    with cols[2]:
        base_branch = st.text_input(
            "Base branch",
            value=settings.get("defaultBaseBranch", "main"),
            key="scheduler_branch",
        )

    install_cmd = (
        "powershell -ExecutionPolicy Bypass -File scripts\\install-scheduled-web-worker.ps1 "
        f'-RepoPath "{repo}" -BaseBranch "{base_branch}" -IntervalHours {interval}'
    )
    with st.expander("Show exact command"):
        st.code(install_cmd, language="powershell")

    button_cols = st.columns(3)
    with button_cols[0]:
        if st.button(
            "Install / Update",
            type="primary",
            use_container_width=True,
            help="Creates or replaces the scheduled task. Requires admin only the first time.",
        ):
            code, out = run_ps(
                "install-scheduled-web-worker.ps1",
                "-RepoPath", repo,
                "-BaseBranch", base_branch,
                "-IntervalHours", str(interval),
                timeout=120,
            )
            action_result("Install Scheduled Worker", code, out)
            if code == 0:
                st.rerun()
    with button_cols[1]:
        if st.button(
            "Remove",
            use_container_width=True,
            disabled=not installed,
            help="Disables and unregisters the scheduled task.",
        ):
            code, out = run_ps("remove-scheduled-web-worker.ps1", timeout=60)
            action_result("Remove Scheduled Worker", code, out)
            if code == 0:
                st.rerun()
    with button_cols[2]:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    st.caption(
        "The scheduled worker only runs the same conservative branch-based pass that the "
        "Run Worker button on Home runs. It never commits or pushes."
    )
