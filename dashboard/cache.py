"""
Cache Module
============
Simple in-memory caching using Streamlit's session state.
"""
import time
from typing import Any

import streamlit as st

from config import CACHE_TTL


def get_cached(key: str, ttl_key: str) -> Any:
    """Get cached value if not expired."""
    cache_key = f"cache_{key}"
    time_key = f"cache_time_{key}"

    if cache_key in st.session_state and time_key in st.session_state:
        elapsed = time.time() - st.session_state[time_key]
        if elapsed < CACHE_TTL.get(ttl_key, 30):
            return st.session_state[cache_key]
    return None


def set_cached(key: str, value: Any) -> None:
    """Set cached value with timestamp."""
    st.session_state[f"cache_{key}"] = value
    st.session_state[f"cache_time_{key}"] = time.time()


def invalidate_cache(pattern: str | None = None) -> None:
    """Invalidate cache entries matching pattern."""
    keys_to_remove = []
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("cache_"):
            if pattern is None or pattern in key:
                keys_to_remove.append(key)
    for key in keys_to_remove:
        del st.session_state[key]


def clear_all_cache() -> None:
    """Clear all cached data."""
    invalidate_cache()