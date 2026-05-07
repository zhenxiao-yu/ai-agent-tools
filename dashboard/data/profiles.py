"""
Profiles Module
===============
Model profile management.
"""
from cache import get_cached, set_cached
from config import PROFILES_FILE, CACHE_TTL
from utils import load_json_file


def load_profiles() -> dict:
    """Load model profiles with caching."""
    cached = get_cached("profiles", "profiles")
    if cached:
        return cached

    result = load_json_file(PROFILES_FILE, {})
    set_cached("profiles", result)
    return result


def get_paid_profiles() -> dict:
    """Get only paid provider profiles."""
    return {k: v for k, v in load_profiles().items() if v.get("paid")}


def get_profile_choices() -> list[tuple[str, str, dict]]:
    """Get list of (display_name, model_id, profile) tuples."""
    profiles = load_profiles()
    choices = []
    for name, profile in profiles.items():
        display = f"{profile.get('provider', 'unknown').title()}"
        if profile.get('paid'):
            display += " 💳"
        else:
            display += " 🆓"
        model_id = f"{profile.get('provider')}/{profile.get('model')}"
        choices.append((display, model_id, profile))
    return choices


def get_profile_by_model_id(model_id: str) -> dict | None:
    """Get profile by model ID (provider/model)."""
    for name, profile in load_profiles().items():
        pid = f"{profile.get('provider')}/{profile.get('model')}"
        if pid == model_id:
            return profile
    return None