"""
Reports Page
============
Surfaces worker, reviewer, doctor, and validation outputs that previously only
existed on disk. Lets the user triage recent runs without leaving the dashboard.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import streamlit as st

from dashboard.config import LOGS, REPORTS, TEAM_REPORTS
from dashboard.ui.components import card_grid, chip, section_header
from dashboard.utils import file_preview, latest_files


REPORT_CATEGORIES: list[dict] = [
    {
        "key": "worker",
        "label": "Worker Runs",
        "folder": REPORTS,
        "patterns": ["web-ai-worker-*.md"],
        "tone": "ready",
        "icon": "🤖",
    },
    {
        "key": "dry_run",
        "label": "Dry Runs",
        "folder": REPORTS,
        "patterns": ["web-ai-dry-run-*.md"],
        "tone": "info",
        "icon": "🧪",
    },
    {
        "key": "review",
        "label": "Reviews",
        "folder": TEAM_REPORTS,
        "patterns": ["review-*.md"],
        "tone": "ready",
        "icon": "🔍",
    },
    {
        "key": "doctor",
        "label": "Doctor / Health",
        "folder": REPORTS,
        "patterns": ["doctor-*.md", "repo-health-*.md", "repo-validation-*.md"],
        "tone": "info",
        "icon": "🩺",
    },
    {
        "key": "audit",
        "label": "Audits",
        "folder": REPORTS,
        "patterns": ["repo-audit-*.md"],
        "tone": "info",
        "icon": "📋",
    },
]


def _gather(category: dict, limit: int = 20) -> list[Path]:
    folder: Path = category["folder"]
    items: list[Path] = []
    for pattern in category["patterns"]:
        items.extend(latest_files(folder, limit, pattern))
    return sorted(items, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def _format_age(path: Path) -> str:
    delta = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _outcome_chip(text: str) -> tuple[str, str]:
    """Best-effort extraction of an outcome chip from a report's contents."""
    lowered = text.lower()
    if re.search(r"\bapprove\b", lowered) and "request changes" not in lowered and "reject" not in lowered:
        return "Approved", "ready"
    if "request changes" in lowered:
        return "Request Changes", "warn"
    if "reject" in lowered:
        return "Rejected", "danger"
    if re.search(r"\b(error|fail|failed|refused)\b", lowered):
        return "Failed", "danger"
    if "dry-run-ok" in lowered or "dry run" in lowered:
        return "Dry Run", "info"
    if "completed-review-required" in lowered or "completed" in lowered:
        return "Completed", "ready"
    return "Recorded", "info"


def render() -> None:
    """Render reports page."""
    section_header(
        "Reports",
        "Worker, reviewer, and health outputs in one place",
        [("Daily Triage", "ready"), ("Local-Only", "info")],
    )

    # Top-level counts
    counts = []
    for cat in REPORT_CATEGORIES:
        items = _gather(cat, limit=200)
        counts.append({
            "title": cat["label"],
            "value": str(len(items)),
            "detail": cat["folder"].name + " / " + ", ".join(cat["patterns"]),
            "tone": cat["tone"],
            "icon": cat["icon"],
        })
    card_grid(counts)

    # Filter UI
    cols = st.columns([2, 2, 1])
    with cols[0]:
        category_labels = ["All"] + [c["label"] for c in REPORT_CATEGORIES]
        selected_label = st.selectbox("Category", category_labels)
    with cols[1]:
        search = st.text_input("Filter by filename or content snippet", placeholder="e.g. web-agent-test, ERROR")
    with cols[2]:
        max_items = st.selectbox("Show", [10, 25, 50], index=1)

    # Aggregate
    if selected_label == "All":
        active_cats = REPORT_CATEGORIES
    else:
        active_cats = [c for c in REPORT_CATEGORIES if c["label"] == selected_label]

    rows: list[tuple[Path, dict]] = []
    for cat in active_cats:
        for path in _gather(cat, limit=max_items * 2):
            rows.append((path, cat))

    rows.sort(key=lambda pair: pair[0].stat().st_mtime, reverse=True)
    rows = rows[: int(max_items)]

    if search:
        needle = search.lower()
        filtered: list[tuple[Path, dict]] = []
        for path, cat in rows:
            if needle in path.name.lower():
                filtered.append((path, cat))
                continue
            try:
                preview = path.read_text(encoding="utf-8", errors="replace")[:8000].lower()
            except Exception:
                preview = ""
            if needle in preview:
                filtered.append((path, cat))
        rows = filtered

    if not rows:
        st.info("No reports match the current filter. Run a worker, reviewer, or doctor pass to populate this page.")
        return

    # Pre-select report from session state (e.g. when home page deep-links here)
    requested = st.session_state.pop("reports_focus_path", None)
    if requested:
        try:
            wanted = Path(requested).resolve()
            for path, _cat in rows:
                if path.resolve() == wanted:
                    st.session_state["reports_selected_path"] = str(path)
                    break
        except Exception:
            pass

    selected_path_str = st.session_state.get("reports_selected_path")

    st.markdown("### Recent Reports")
    for path, cat in rows:
        is_active = selected_path_str == str(path)
        try:
            preview_text = path.read_text(encoding="utf-8", errors="replace")[:4000]
        except Exception:
            preview_text = ""
        outcome_label, outcome_tone = _outcome_chip(preview_text)
        cat_chip = chip(cat["label"], cat["tone"])
        outcome = chip(outcome_label, outcome_tone)
        age = _format_age(path)

        cols = st.columns([6, 2, 1])
        with cols[0]:
            st.markdown(
                f"**{path.name}**  \n"
                f"<span style='color: var(--text-secondary); font-size: 0.85rem'>"
                f"{cat_chip} &nbsp; {outcome} &nbsp; · &nbsp; {age}"
                f"</span>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.caption(str(path.relative_to(path.parents[1])) if len(path.parents) >= 2 else path.name)
        with cols[2]:
            label = "Hide" if is_active else "View"
            if st.button(label, key=f"view_{path.name}"):
                st.session_state["reports_selected_path"] = None if is_active else str(path)
                st.rerun()

    # Detail pane
    selected_path_str = st.session_state.get("reports_selected_path")
    if selected_path_str:
        selected = Path(selected_path_str)
        if selected.exists():
            st.markdown("---")
            st.markdown(f"### {selected.name}")
            mtime = datetime.fromtimestamp(selected.stat().st_mtime)
            st.caption(
                f"{selected} · last updated {mtime:%Y-%m-%d %H:%M:%S} · "
                f"{selected.stat().st_size / 1024:.1f} KB"
            )
            content = file_preview(selected, 60000)
            if selected.suffix.lower() == ".md":
                st.markdown(content)
            else:
                st.code(content, language="text")

    # Recent log tail
    with st.expander("Recent Worker / Reviewer Logs"):
        log_files = latest_files(LOGS, 10, "web-ai-*.log")
        if not log_files:
            st.caption("No worker logs yet. The Run Worker action on Home will populate this.")
        for log in log_files:
            st.markdown(f"**{log.name}** · {_format_age(log)}")
            st.code(file_preview(log, 4000), language="text")
