"""
Settings Module
===============
Dashboard settings management with caching.
"""
import json

import streamlit as st

from dashboard.cache import get_cached, set_cached, invalidate_cache
from dashboard.config import SETTINGS_FILE, DEFAULT_SETTINGS
from dashboard.utils import load_json_file, save_json_file, log_event, validate_branch_name


def normalize_settings(data: dict | None) -> dict:
    """Normalize and validate settings data."""
    source = data or {}
    settings = DEFAULT_SETTINGS.copy()
    settings.update({k: v for k, v in source.items() if k in settings})

    if not isinstance(settings.get("defaultModel"), str) or not settings["defaultModel"].strip():
        settings["defaultModel"] = DEFAULT_SETTINGS["defaultModel"]

    ok, _ = validate_branch_name(str(settings.get("defaultBaseBranch", "")))
    if not ok:
        settings["defaultBaseBranch"] = DEFAULT_SETTINGS["defaultBaseBranch"]

    if settings.get("defaultIntervalHours") not in {1, 2, 4, 8}:
        settings["defaultIntervalHours"] = DEFAULT_SETTINGS["defaultIntervalHours"]

    settings["safetyMode"] = bool(settings.get("safetyMode", True))
    settings["advancedMode"] = bool(settings.get("advancedMode", False))
    settings["autoRouting"] = bool(settings.get("autoRouting", True))
    settings["compactView"] = bool(settings.get("compactView", False))
    settings["theme"] = settings.get("theme") if settings.get("theme") in {"dark"} else DEFAULT_SETTINGS["theme"]
    return settings


def load_settings() -> dict:
    """Load settings with caching."""
    cached = get_cached("settings", "settings")
    if cached:
        return cached

    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")

    try:
        data = load_json_file(SETTINGS_FILE, {})
        result = normalize_settings(data)
    except Exception as exc:
        log_event("settings_error", "Failed to load dashboard settings", {"error": str(exc)})
        result = normalize_settings({})

    set_cached("settings", result)
    return result


def save_settings(settings: dict) -> None:
    """Save settings and invalidate cache."""
    normalized = normalize_settings(settings)
    save_json_file(SETTINGS_FILE, normalized)
    invalidate_cache("settings")


def get_default_model() -> str:
    """Get the current default model."""
    return load_settings().get("defaultModel", "ollama/qwen2.5-coder:14b")


def get_default_branch() -> str:
    """Get the current default base branch."""
    return load_settings().get("defaultBaseBranch", "main")


def is_safety_mode() -> bool:
    """Check if safety mode is enabled."""
    return load_settings().get("safetyMode", True)
