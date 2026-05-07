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
          --bg: #0a0e14;
          --panel: #0f1419;
          --panel2: #161b22;
          --panel3: #1c2128;
          --line: #30363d;
          --line-hover: #3d444d;
          --green: #3fb950;
          --green-glow: rgba(63, 185, 80, 0.3);
          --cyan: #58a6ff;
          --cyan-glow: rgba(88, 166, 255, 0.3);
          --yellow: #d29922;
          --yellow-glow: rgba(210, 153, 34, 0.3);
          --red: #f85149;
          --red-glow: rgba(248, 81, 73, 0.3);
          --muted: #8b949e;
          --text: #e6edf3;
          --text-secondary: #7d8590;
          --font: "Segoe UI", "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background: linear-gradient(135deg, #0a0e14 0%, #0d1117 50%, #0a0e14 100%);
            color: var(--text);
            font-family: var(--font);
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

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
        }

        /* Hero Section */
        .hero {
            position: relative;
            background: linear-gradient(135deg, rgba(13, 17, 23, 0.95) 0%, rgba(10, 14, 20, 0.98) 100%);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, var(--green), var(--cyan), var(--green));
            opacity: 0.7;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #fff 0%, var(--cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }
        .hero p {
            color: var(--text-secondary);
            margin: 0.75rem 0 0;
            font-size: 1.1rem;
            line-height: 1.6;
        }

        /* Top Banner */
        .top-banner {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border: 1px solid rgba(63, 185, 80, 0.3);
            background: rgba(46, 160, 67, 0.1);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            color: #aff5b4;
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
        }

        /* Page Header */
        .page-head {
            background: linear-gradient(135deg, var(--panel2) 0%, var(--panel) 100%);
            border: 1px solid var(--line);
            border-radius: 12px;
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
            background: rgba(15, 20, 25, 0.92);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }

        .dock-panel {
            background: linear-gradient(180deg, var(--panel2) 0%, var(--panel) 100%);
            border: 1px solid var(--line);
            border-radius: 14px;
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
            background: linear-gradient(135deg, var(--panel2) 0%, var(--panel) 100%);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.9rem 1rem 0.6rem;
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
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            border: 1px solid var(--line);
            background: linear-gradient(135deg, var(--panel2) 0%, var(--panel) 100%);
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
            border: 1px solid rgba(88, 166, 255, 0.35);
            background: rgba(88, 166, 255, 0.1);
            color: #d6ecff;
            padding: 1rem 1.1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            line-height: 1.55;
        }

        .flow-lane {
            min-height: 148px;
            border-radius: 14px;
            padding: 1rem;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel2) 0%, var(--panel) 100%);
            margin-bottom: 1rem;
        }

        .lane-ready { border-color: rgba(63, 185, 80, 0.35); }
        .lane-info { border-color: rgba(88, 166, 255, 0.35); }
        .lane-warn { border-color: rgba(210, 153, 34, 0.35); }

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
        }

        .mc-card {
            display: flex;
            flex-direction: column;
            background: linear-gradient(180deg, var(--panel2) 0%, var(--panel) 100%);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.25rem;
            min-height: 140px;
            transition: all 0.2s ease;
            overflow: hidden;
            position: relative;
        }
        .mc-card:hover {
            border-color: var(--line-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }
        .mc-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 3px; height: 100%;
            opacity: 0;
            transition: opacity 0.2s ease;
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
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
            flex-grow: 1;
        }
        .card-detail {
            color: var(--muted);
            font-size: 0.875rem;
            margin-top: auto;
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
            border-radius: 20px;
            padding: 0.35rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid var(--line);
            background: var(--panel2);
            transition: all 0.15s ease;
        }
        .chip:hover { transform: scale(1.02); }
        .chip-ready { color: #aff5b4; border-color: rgba(63, 185, 80, 0.4); background: rgba(63, 185, 80, 0.1); }
        .chip-warn { color: #ffd700; border-color: rgba(210, 153, 34, 0.4); background: rgba(210, 153, 34, 0.1); }
        .chip-danger { color: #ff7b72; border-color: rgba(248, 81, 73, 0.4); background: rgba(248, 81, 73, 0.1); }
        .chip-info { color: #79c0ff; border-color: rgba(88, 166, 255, 0.4); background: rgba(88, 166, 255, 0.1); }
        .chip-muted { color: var(--muted); border-color: var(--line); background: var(--panel2); }

        /* Buttons */
        div[data-testid="stButton"] button {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel2) 0%, var(--panel) 100%);
            color: var(--text);
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.15s ease;
        }
        div[data-testid="stButton"] button:hover {
            border-color: var(--cyan);
            background: linear-gradient(180deg, var(--panel3) 0%, var(--panel2) 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
        }
        div[data-testid="stButton"] button:active { transform: translateY(0); }

        div[data-testid="stHorizontalBlock"] > div:has(> div[data-testid="stRadio"]) {
            width: 100%;
        }

        div[data-testid="stRadio"] label p {
            font-size: 0.95rem;
        }

        .stCode pre, code, pre {
            white-space: pre-wrap !important;
            word-break: break-word;
        }

        /* Primary Button */
        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(180deg, var(--cyan) 0%, #0969da 100%);
            border-color: var(--cyan);
            color: white;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: linear-gradient(180deg, #79c0ff 0%, var(--cyan) 100%);
            box-shadow: 0 4px 12px var(--cyan-glow);
        }

        /* Project Cards */
        .project-card {
            background: linear-gradient(135deg, var(--panel2) 0%, var(--panel) 100%);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .project-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--green), var(--cyan));
        }
        .project-card.blocked::before { background: var(--red); }
        .project-card.warning::before { background: var(--yellow); }

        /* Key Input Group */
        .key-input-group {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.25rem;
            margin: 0.75rem 0;
        }

        /* Model Card */
        .model-card {
            background: var(--panel2);
            border: 2px solid var(--line);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .model-card:hover { border-color: var(--cyan); background: var(--panel3); }
        .model-card.selected { border-color: var(--green); background: rgba(63, 185, 80, 0.1); }
        .model-card.disabled { opacity: 0.5; cursor: not-allowed; }

        /* Animations */
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-in { animation: slideIn 0.3s ease-out; }

        /* Responsive */
        @media (max-width: 768px) {
            .card-grid { grid-template-columns: 1fr; }
            .hero h1 { font-size: 1.75rem; }
            .hero { padding: 1.5rem; }
            .top-banner { align-items: flex-start; }
            .flow-lane { min-height: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
