"""
Keys Module
===========
Environment key management for API providers.
"""
import streamlit as st

from cache import get_cached
from utils import ps_inline


def key_present(env_var: str | None) -> bool:
    """Check if environment variable is set (cached per session)."""
    if not env_var:
        return False

    cache_key = f"key_present_{env_var}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    code, out = ps_inline(
        f"[Environment]::GetEnvironmentVariable('{env_var}','User')",
        timeout=5
    )
    present = bool(out.strip())
    st.session_state[cache_key] = present
    return present


def set_env_key(env_var: str, value: str) -> bool:
    """Set environment variable at user level."""
    try:
        code, _ = ps_inline(
            f"[Environment]::SetEnvironmentVariable('{env_var}', '{value}', 'User')",
            timeout=10
        )
        # Invalidate cache
        cache_key = f"key_present_{env_var}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        return code == 0
    except Exception as exc:
        return False


def remove_env_key(env_var: str) -> bool:
    """Remove environment variable at user level."""
    try:
        code, _ = ps_inline(
            f"[Environment]::SetEnvironmentVariable('{env_var}', $null, 'User')",
            timeout=10
        )
        # Invalidate cache
        cache_key = f"key_present_{env_var}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        return code == 0
    except Exception as exc:
        return False