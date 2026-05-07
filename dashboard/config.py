"""
Dashboard Configuration
=======================
Central configuration module for the Local AI Mission Control Dashboard.
"""
import re
from pathlib import Path
from typing import Any

# ============================================
# PATHS
# ============================================
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
TEAM_REPORTS = ROOT / "team" / "reports"
CONFIGS = ROOT / "configs"

# Data files
ALLOWLIST_FILE = CONFIGS / "repo-allowlist.txt"
PROFILES_FILE = CONFIGS / "model-profiles.json"
SETTINGS_FILE = CONFIGS / "dashboard-settings.json"

# ============================================
# DEFAULTS
# ============================================
DEFAULT_SETTINGS = {
    "defaultModel": "ollama/qwen2.5-coder:14b",
    "defaultBaseBranch": "main",
    "defaultIntervalHours": 2,
    "safetyMode": True,
    "advancedMode": False,
    "autoRouting": True,
    "theme": "dark",
    "compactView": False,
}

# ============================================
# CACHE CONFIGURATION
# ============================================
CACHE_TTL = {
    "service_status": 45,   # Service status refreshes every 45s
    "profiles": 300,        # Model profiles rarely change
    "settings": 60,         # Settings can change occasionally
    "issues": 15,           # Issues check more frequently
    "keys": 60,             # Environment key checks
}

# ============================================
# SECURITY
# ============================================
SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_\-]{12,})"),
    re.compile(r"(gho_[A-Za-z0-9_\-]{12,})"),
    re.compile(r"((?:API_KEY|TOKEN|SECRET|PASSWORD)\s*[=:]\s*)[^\s]+", re.I),
    re.compile(r"([A-Za-z0-9_\-]{32,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,})"),
]

# ============================================
# UI CONSTANTS
# ============================================
PAGE_ICONS = {
    "Home": "🏠",
    "Automation": "🧠",
    "Fix Center": "🔧",
    "Tools / Integrations": "🛠️",
    "Workflow Wizard": "🧙",
    "Projects": "📁",
    "Vibe Code": "✨",
    "Runs": "📊",
    "Morning Review": "🌅",
    "Scheduler": "⏰",
    "Models": "🤖",
    "Providers": "💳",
    "Logs & Reports": "📋",
    "VS Code": "📝",
    "Settings": "⚙️",
    "Help": "❓",
}

STATUS_ICONS = {
    "ready": "🟢",
    "warn": "🟡",
    "danger": "🔴",
    "info": "🔵",
    "muted": "⚪",
}

CARD_COLORS = {
    "ready": "#3fb950",
    "warn": "#d29922",
    "danger": "#f85149",
    "info": "#58a6ff",
    "muted": "#8b949e",
}
