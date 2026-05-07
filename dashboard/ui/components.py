"""
Components Module
=================
Reusable UI components for the dashboard.
"""
from html import escape

import streamlit as st
from dashboard.utils import log_event


def chip(label: str, tone: str = "muted") -> str:
    """Render a status chip."""
    return f'<span class="chip chip-{tone}">{escape(label)}</span>'


def card_html(title: str, value: str, detail: str = "", tone: str = "info", icon: str = "") -> str:
    """Build card HTML for standalone renderers and card grids."""
    icon_html = f'<span class="card-icon" aria-hidden="true">{escape(icon)}</span>' if icon else ""
    return f"""
    <article class="mc-card card-{tone} animate-in">
        <div class="card-header">
            {icon_html}
            <div class="card-kicker">{escape(title)}</div>
        </div>
        <div class="card-value">{escape(value)}</div>
        <div class="card-detail">{escape(detail)}</div>
    </article>
    """


def card(title: str, value: str, detail: str = "", tone: str = "info", icon: str = "") -> None:
    """Render a stat card with uniform height."""
    st.markdown(card_html(title, value, detail, tone, icon), unsafe_allow_html=True)


def card_grid(items: list[dict[str, str]]) -> None:
    """Render a responsive grid of equal-height cards."""
    cards = "".join(
        card_html(
            item.get("title", ""),
            item.get("value", ""),
            item.get("detail", ""),
            item.get("tone", "info"),
            item.get("icon", ""),
        )
        for item in items
    )
    st.markdown(f'<section class="card-grid">{cards}</section>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", chips: list[tuple[str, str]] | None = None) -> None:
    """Render section header with optional chips."""
    chip_html = " ".join(chip(label, tone) for label, tone in (chips or []))
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""

    st.markdown(f"""
    <div class="page-head animate-in">
        <h2>{escape(title)}</h2>
        {subtitle_html}
        <div class="chip-container">{chip_html}</div>
    </div>
    """, unsafe_allow_html=True)


def action_result(label: str, code: int, out: str) -> None:
    """Display action result."""
    if code == 0:
        st.success(f"{label}: Completed")
    else:
        st.error(f"{label}: Failed")
    with st.expander("Output", expanded=code != 0):
        st.code(out or "(no output)")


def quick_action(label: str, script: str, args: list[str] | None = None, help_text: str = "", timeout: int = 240) -> None:
    """Quick action button."""
    from dashboard.utils import run_ps
    args = args or []
    if st.button(label, key=f"qa_{label.replace(' ', '_')}", help=help_text, use_container_width=True):
        code, out = run_ps(script, *args, timeout=timeout)
        action_result(label, code, out)


def model_status_badge(is_ready: bool, text: str) -> str:
    """Generate status badge for model."""
    tone = "ready" if is_ready else "warn"
    return chip(text, tone)


def provider_card_header(provider: str, model: str, role: str, has_key: bool) -> None:
    """Render provider card header with key status."""
    status = "Key Configured" if has_key else "Key Missing"
    tone = "ready" if has_key else "warn"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
            <h3 style="margin: 0;">{escape(provider)}</h3>
            <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem;">
                <code translate="no">{escape(model)}</code> {'&middot; ' + escape(role) if role else ''}
            </p>
        </div>
        <div>{chip(status, tone)}</div>
    </div>
    """, unsafe_allow_html=True)


def info_panel(title: str, body: str, tone: str = "info") -> None:
    """Render a compact information panel."""
    safe_body = escape(body).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="info-panel panel-{tone}">
            <div class="info-panel-title">{escape(title)}</div>
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
        st.error(f"{title} failed to render")
        if help_text:
            st.caption(help_text)
        with st.expander("Diagnostic details"):
            st.exception(exc)
