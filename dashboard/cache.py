"""
Cache Module
============
Simple in-memory caching using Streamlit's session state.
"""
import time
from typing import Any

import streamlit as st

from dashboard.config import CACHE_TTL


def _session_state():
    """Return session state when Streamlit runtime is available."""
    try:
        return st.session_state
    except Exception:
        return None


def get_cached(key: str, ttl_key: str) -> Any:
    """Get cached value if not expired."""
    cache_key = f"cache_{key}"
    time_key = f"cache_time_{key}"
    session_state = _session_state()
    if session_state is None:
        return None

    if cache_key in session_state and time_key in session_state:
        elapsed = time.time() - session_state[time_key]
        if elapsed < CACHE_TTL.get(ttl_key, 30):
            return session_state[cache_key]
    return None


def set_cached(key: str, value: Any) -> None:
    """Set cached value with timestamp."""
    session_state = _session_state()
    if session_state is None:
        return
    session_state[f"cache_{key}"] = value
    session_state[f"cache_time_{key}"] = time.time()


def invalidate_cache(pattern: str | None = None) -> None:
    """Invalidate cache entries matching pattern."""
    session_state = _session_state()
    if session_state is None:
        return
    keys_to_remove = []
    for key in list(session_state.keys()):
        if isinstance(key, str) and key.startswith("cache_"):
            if pattern is None or pattern in key:
                keys_to_remove.append(key)
    for key in keys_to_remove:
        del session_state[key]


def clear_all_cache() -> None:
    """Clear all cached data."""
    invalidate_cache()
