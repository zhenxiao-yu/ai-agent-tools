"""
Runs Page
=========
Live status of asynchronously submitted jobs (worker, reviewer, dry run,
pipeline) plus their recent history. Cancels active jobs and shows the
captured log tail for completed ones.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from dashboard import jobs as jobs_mod
from dashboard.ui.components import card_grid, chip, section_header


_TONE_BY_STATUS = {
    "queued": "muted",
    "running": "info",
    "completed": "ready",
    "failed": "danger",
    "cancelled": "warn",
}


def _tone(status: str) -> str:
    return _TONE_BY_STATUS.get(status, "muted")


def _format_elapsed(start: str, end: str = "") -> str:
    if not start:
        return "—"
    try:
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end) if end else datetime.now()
        secs = max(0, int((e - s).total_seconds()))
    except Exception:
        return "—"
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m {secs % 60:02d}s"
    return f"{secs // 3600}h {(secs % 3600) // 60:02d}m"


def render() -> None:
    section_header(
        "Runs",
        "Background jobs you submitted from the dashboard",
        [("Async", "info"), ("Live Status", "ready")],
    )

    summary = jobs_mod.counts()
    card_grid([
        {"title": "Running", "value": str(summary.get("running", 0)), "detail": "In flight now", "tone": "info"},
        {"title": "Completed", "value": str(summary.get("completed", 0)), "detail": "Finished cleanly", "tone": "ready"},
        {"title": "Failed", "value": str(summary.get("failed", 0)), "detail": "Non-zero exit", "tone": "danger" if summary.get("failed", 0) else "muted"},
        {"title": "Cancelled", "value": str(summary.get("cancelled", 0)), "detail": "Stopped by you", "tone": "warn" if summary.get("cancelled", 0) else "muted"},
    ])

    control_cols = st.columns([1, 1, 1, 2])
    with control_cols[0]:
        if st.button("Refresh", use_container_width=True, help="Re-read job state from disk."):
            st.rerun()
    with control_cols[1]:
        auto_refresh = st.toggle(
            "Auto refresh",
            value=st.session_state.get("runs_auto_refresh", False),
            key="runs_auto_refresh",
            help="Re-render every few seconds while jobs are active.",
        )
    with control_cols[2]:
        if st.button("Cleanup", use_container_width=True, help="Keep the most recent 50 records and remove older ones."):
            removed = jobs_mod.cleanup_old(50)
            st.success(f"Removed {removed} old job records.")
            st.rerun()
    with control_cols[3]:
        st.caption(f"Job records live in {jobs_mod.JOBS_DIR}.")

    all_jobs = jobs_mod.list_jobs(limit=100)
    active = [j for j in all_jobs if j.status in jobs_mod.ACTIVE_STATES]
    history = [j for j in all_jobs if j.status not in jobs_mod.ACTIVE_STATES]

    # Active jobs
    st.markdown("### Active")
    if not active:
        st.info(
            "No jobs running. Use the Run on a Project section on Home or the "
            "Run Pipeline button to start one."
        )
    else:
        for job in active:
            cols = st.columns([5, 2, 2, 1, 1])
            with cols[0]:
                st.markdown(f"**{job.label}**")
                st.caption(f"{job.id} · {job.repo or '—'}")
            with cols[1]:
                st.markdown(chip(job.status, _tone(job.status)), unsafe_allow_html=True)
            with cols[2]:
                st.caption(f"Elapsed: {_format_elapsed(job.started_at or job.submitted_at)}")
            with cols[3]:
                if st.button("Tail", key=f"tail_{job.id}", use_container_width=True):
                    st.session_state["runs_open_log"] = job.id
                    st.rerun()
            with cols[4]:
                if st.button("Cancel", key=f"cancel_{job.id}", use_container_width=True):
                    jobs_mod.cancel(job.id)
                    st.rerun()

    # Live log pane (if a job is selected)
    open_id = st.session_state.get("runs_open_log")
    if open_id:
        focus_job = jobs_mod.get(open_id)
        if focus_job:
            st.markdown("---")
            st.markdown(f"### Log — {focus_job.label}")
            st.caption(
                f"{focus_job.id} · status: {focus_job.status} · "
                f"exit: {focus_job.exit_code if focus_job.exit_code is not None else '—'} · "
                f"log: {focus_job.log_path}"
            )
            log_text = jobs_mod.tail(focus_job.id, max_chars=20000)
            st.code(log_text or "(no output captured yet)", language="text")
            close_cols = st.columns([1, 5])
            with close_cols[0]:
                if st.button("Close log", use_container_width=True):
                    st.session_state.pop("runs_open_log", None)
                    st.rerun()

    # History
    st.markdown("### Recent")
    if not history:
        st.caption("No completed jobs yet.")
    else:
        for job in history[:25]:
            elapsed = _format_elapsed(job.started_at or job.submitted_at, job.ended_at)
            ended = (job.ended_at or job.submitted_at).replace("T", " ")
            header = f"{job.label} · {job.status} · {elapsed} · {ended}"
            with st.expander(header):
                st.caption(
                    f"ID: {job.id} · Repo: {job.repo or '—'} · "
                    f"Exit: {job.exit_code if job.exit_code is not None else '—'} · "
                    f"Script: {job.script}"
                )
                log_text = jobs_mod.tail(job.id, max_chars=18000)
                if log_text:
                    st.code(log_text, language="text")
                else:
                    log_path = Path(job.log_path) if job.log_path else None
                    if log_path and not log_path.exists():
                        st.caption("Wrapper log file is missing (cleaned up?).")
                    else:
                        st.caption("No output was captured for this job.")

    # Auto-refresh tick. Only burn cycles while something is in flight.
    if auto_refresh and active:
        import time
        time.sleep(3)
        st.rerun()
