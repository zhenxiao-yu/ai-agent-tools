"""
Settings Module
===============
Dashboard settings management with caching.
"""
import streamlit as st

from cache import get_cached, set_cached, invalidate_cache
from config import SETTINGS_FILE, DEFAULT_SETTINGS, CACHE_TTL
from utils import load_json_file, save_json_file


def load_settings() -> dict:
    """Load settings with caching."""
    cached = get_cached("settings", "settings")
    if cached:
        return cached

    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(__import__("json").dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")

    try:
        data = load_json_file(SETTINGS_FILE, {})
        result = {**DEFAULT_SETTINGS, **data}
    except Exception:
        result = DEFAULT_SETTINGS.copy()

    set_cached("settings", result)
    return result


def save_settings(settings: dict) -> None:
    """Save settings and invalidate cache."""
    save_json_file(SETTINGS_FILE, settings)
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