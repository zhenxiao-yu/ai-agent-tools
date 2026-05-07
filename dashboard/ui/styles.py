"""
Styles Module
=============
CSS styles for the dashboard with uniform card heights and responsive design.
"""

import streamlit as st


def render_styles():
    """Render all CSS styles."""
    st.markdown(
        """
        <style>
        :root {
          --bg: #11151b;
          --panel: #171c24;
          --panel2: #1b212b;
          --panel3: #222a36;
          --line: #2a3340;
          --line-hover: #3a4657;
          --green: #68b36b;
          --cyan: #73a8ff;
          --yellow: #c8a44f;
          --red: #d46a6a;
          --muted: #95a0ad;
          --text: #edf1f7;
          --text-secondary: #a0acb9;
          --font: "Segoe UI", "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif;
        }

        html {
            color-scheme: dark;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: var(--font);
            overflow-x: hidden;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--panel); }
        ::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--line-hover); }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: var(--panel);
            border-right: 1px solid var(--line);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        /* Hero Section */
        .hero {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 650;
            color: var(--text);
            letter-spacing: 0;
            text-wrap: balance;
        }
        .hero p {
            color: var(--text-secondary);
            margin: 0.55rem 0 0;
            font-size: 1rem;
            line-height: 1.5;
        }

        /* Top Banner */
        .top-banner {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            font-size: 0.92rem;
        }

        /* Page Header */
        .page-head {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.5rem;
        }
        .page-head h2 {
            margin: 0 0 0.5rem;
            color: var(--text);
            font-size: 1.5rem;
            font-weight: 600;
        }
        .page-head p {
            color: var(--text-secondary);
            margin: 0 0 0.75rem;
            font-size: 0.95rem;
        }
        .chip-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .diagnostic-panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }

        .dock-panel {
            background: var(--panel2);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .dock-title {
            font-size: 0.8rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            letter-spacing: 0.08em;
            margin-bottom: 0.6rem;
            font-weight: 700;
        }

        .status-list {
            margin: 0;
            padding-left: 1.1rem;
            color: var(--text-secondary);
        }

        .top-nav-wrap {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem 1rem 0.65rem;
            margin-bottom: 1rem;
        }

        .top-nav-title {
            color: var(--text-secondary);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }

        .info-panel {
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            border: 1px solid var(--line);
            background: var(--panel);
        }

        .info-panel-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
            margin-bottom: 0.45rem;
            font-weight: 700;
        }

        .info-panel-body {
            color: var(--text);
            line-height: 1.55;
        }

        .insight-panel {
            border: 1px solid rgba(115, 168, 255, 0.35);
            background: rgba(115, 168, 255, 0.08);
            color: var(--text);
            padding: 1rem 1.1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            line-height: 1.55;
        }

        .flow-lane {
            min-height: 156px;
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid var(--line);
            background: var(--panel);
            margin-bottom: 1rem;
            height: 100%;
        }

        .lane-ready { border-color: rgba(104, 179, 107, 0.35); }
        .lane-info { border-color: rgba(115, 168, 255, 0.35); }
        .lane-warn { border-color: rgba(200, 164, 79, 0.35); }

        .flow-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.55rem;
        }

        .flow-detail {
            color: var(--text-secondary);
            line-height: 1.55;
            font-size: 0.92rem;
        }

        /* ============================================
           CARDS - UNIFORM HEIGHT
           ============================================ */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
            align-items: stretch;
        }

        .mc-card {
            display: flex;
            flex-direction: column;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.25rem;
            min-height: 148px;
            height: 100%;
            transition: border-color 0.16s ease, background-color 0.16s ease, box-shadow 0.16s ease;
            overflow: hidden;
            position: relative;
        }
        .mc-card:hover {
            border-color: var(--line-hover);
            background: var(--panel2);
            box-shadow: 0 0 0 1px rgba(115, 168, 255, 0.08);
        }
        .mc-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 3px; height: 100%;
            opacity: 0;
            transition: opacity 0.16s ease;
        }
        .mc-card:hover::before { opacity: 1; }
        .card-ready::before { background: var(--green); }
        .card-warn::before { background: var(--yellow); }
        .card-danger::before { background: var(--red); }
        .card-info::before { background: var(--cyan); }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .card-icon {
            font-size: 1.25rem;
            width: 24px;
            text-align: center;
        }
        .card-kicker {
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
        }
        .card-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
            flex-grow: 1;
            font-variant-numeric: tabular-nums;
            text-wrap: balance;
        }
        .card-detail {
            color: var(--muted);
            font-size: 0.875rem;
            margin-top: auto;
            line-height: 1.5;
        }
        .card-ready .card-value { color: var(--green); }
        .card-warn .card-value { color: var(--yellow); }
        .card-danger .card-value { color: var(--red); }
        .card-info .card-value { color: var(--cyan); }

        /* Chips */
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 6px;
            padding: 0.35rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid var(--line);
            background: var(--panel2);
            transition: border-color 0.15s ease, background-color 0.15s ease;
        }
        .chip-ready { color: #ccefd1; border-color: rgba(104, 179, 107, 0.4); background: rgba(104, 179, 107, 0.08); }
        .chip-warn { color: #ead9ad; border-color: rgba(200, 164, 79, 0.4); background: rgba(200, 164, 79, 0.08); }
        .chip-danger { color: #f1c0c0; border-color: rgba(212, 106, 106, 0.4); background: rgba(212, 106, 106, 0.08); }
        .chip-info { color: #c9d9ff; border-color: rgba(115, 168, 255, 0.4); background: rgba(115, 168, 255, 0.08); }
        .chip-muted { color: var(--muted); border-color: var(--line); background: var(--panel2); }

        /* Buttons */
        div[data-testid="stButton"] button {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--panel2);
            color: var(--text);
            font-weight: 500;
            padding: 0.5rem 1rem;
            touch-action: manipulation;
            transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
        }
        div[data-testid="stButton"] button:hover {
            border-color: var(--cyan);
            background: var(--panel3);
            box-shadow: 0 0 0 1px rgba(115, 168, 255, 0.12);
        }
        div[data-testid="stButton"] button:focus-visible,
        div[data-testid="stRadio"] input:focus-visible + div {
            outline: 2px solid var(--cyan);
            outline-offset: 2px;
        }

        div[data-testid="stHorizontalBlock"] > div:has(> div[data-testid="stRadio"]) {
            width: 100%;
        }

        div[data-testid="column"] > div {
            height: 100%;
        }

        div[data-testid="stRadio"] label p {
            font-size: 0.95rem;
        }

        div[data-testid="stRadio"] [role="radiogroup"] {
            gap: 0.35rem;
        }

        div[data-testid="stRadio"] label {
            background: var(--panel2);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.4rem 0.8rem;
        }

        .stCode pre, code, pre {
            white-space: pre-wrap !important;
            word-break: break-word;
        }

        /* Primary Button */
        div[data-testid="stButton"] button[kind="primary"] {
            background: var(--cyan);
            border-color: var(--cyan);
            color: #0d1117;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #8bb6ff;
            box-shadow: 0 0 0 1px rgba(115, 168, 255, 0.2);
        }

        /* Project Cards */
        .project-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Key Input Group */
        .key-input-group {
            background: var(--panel2);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.25rem;
            margin: 0 0 1rem;
        }

        /* Model Card */
        .model-card {
            background: var(--panel2);
            border: 2px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: border-color 0.2s ease, background-color 0.2s ease;
        }
        .model-card:hover { border-color: var(--cyan); background: var(--panel3); }
        .model-card.selected { border-color: var(--green); background: rgba(104, 179, 107, 0.08); }
        .model-card.disabled { opacity: 0.5; cursor: not-allowed; }

        /* Animations */
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-in { animation: slideIn 0.3s ease-out; }

        @media (prefers-reduced-motion: reduce) {
            .animate-in {
                animation: none;
            }
            .mc-card,
            .chip,
            div[data-testid="stButton"] button,
            .model-card {
                transition: none;
            }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .card-grid { grid-template-columns: 1fr; }
            .hero h1 { font-size: 1.6rem; }
            .hero { padding: 1.3rem; }
            .top-banner { align-items: flex-start; }
            .flow-lane { min-height: 0; }
            .block-container { padding-left: 0.9rem; padding-right: 0.9rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
