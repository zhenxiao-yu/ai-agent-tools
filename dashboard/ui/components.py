"""
Components Module
=================
Reusable UI components for the dashboard.
"""
import streamlit as st
from dashboard.config import STATUS_ICONS
from dashboard.utils import log_event


def chip(label: str, tone: str = "muted") -> str:
    """Render a status chip."""
    icons = {
        "ready": "✅",
        "warn": "⚠️",
        "danger": "🔴",
        "info": "ℹ️",
        "muted": "•",
    }
    return f'<span class="chip chip-{tone}">{icons.get(tone, "•")} {label}</span>'


def card(title: str, value: str, detail: str = "", tone: str = "info", icon: str = "") -> None:
    """Render a stat card with uniform height."""
    icons = STATUS_ICONS
    icon_html = f'<span class="card-icon">{icons.get(tone, icon)}</span>' if icon or tone in icons else ""

    st.markdown(f"""
    <div class="mc-card card-{tone} animate-in">
        <div class="card-header">
            {icon_html}
            <div class="card-kicker">{title}</div>
        </div>
        <div class="card-value">{value}</div>
        <div class="card-detail">{detail}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", chips: list[tuple[str, str]] | None = None) -> None:
    """Render section header with optional chips."""
    chip_html = " ".join(chip(label, tone) for label, tone in (chips or []))
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""

    st.markdown(f"""
    <div class="page-head animate-in">
        <h2>{title}</h2>
        {subtitle_html}
        <div class="chip-container">{chip_html}</div>
    </div>
    """, unsafe_allow_html=True)


def action_result(label: str, code: int, out: str) -> None:
    """Display action result."""
    if code == 0:
        st.success(f"✅ {label}: Completed")
    else:
        st.error(f"❌ {label}: Failed")
    with st.expander("📋 Output", expanded=code != 0):
        st.code(out or "(no output)")


def quick_action(label: str, script: str, args: list[str] | None = None, help_text: str = "", timeout: int = 240) -> None:
    """Quick action button."""
    from dashboard.utils import run_ps
    args = args or []
    if st.button(label, key=f"qa_{label.replace(' ', '_')}", help=help_text):
        code, out = run_ps(script, *args, timeout=timeout)
        action_result(label, code, out)


def model_status_badge(is_ready: bool, text: str) -> str:
    """Generate status badge for model."""
    tone = "ready" if is_ready else "warn"
    return chip(text, tone)


def provider_card_header(provider: str, model: str, role: str, has_key: bool) -> None:
    """Render provider card header with key status."""
    status = "✅ Key configured" if has_key else "❌ Key missing"
    tone = "ready" if has_key else "warn"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
            <h3 style="margin: 0;">{provider}</h3>
            <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem;">
                <code>{model}</code> • {role}
            </p>
        </div>
        <div>{chip(status, tone)}</div>
    </div>
    """, unsafe_allow_html=True)


def info_panel(title: str, body: str, tone: str = "info") -> None:
    """Render a compact information panel."""
    safe_body = body.replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="info-panel panel-{tone}">
            <div class="info-panel-title">{title}</div>
            <div class="info-panel-body">{safe_body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def error_boundary(title: str, renderer, help_text: str = "") -> None:
    """Render a section with a recoverable error boundary."""
    try:
        renderer()
    except Exception as exc:
        log_event("ui_error_boundary", "Recoverable UI error", {"title": title, "error": str(exc)})
        st.error(f"❌ {title} failed to render")
        if help_text:
            st.caption(help_text)
        with st.expander("Diagnostic details"):
            st.exception(exc)
