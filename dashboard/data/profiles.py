"""
Profiles Module
===============
Model profile management.
"""
from dashboard.cache import get_cached, set_cached
from dashboard.config import PROFILES_FILE
from dashboard.utils import load_json_file, log_event


def _is_valid_profile(profile: dict) -> bool:
    return bool(profile.get("provider")) and bool(profile.get("model"))


def load_profiles() -> dict:
    """Load model profiles with caching."""
    cached = get_cached("profiles", "profiles")
    if cached:
        return cached

    result = load_json_file(PROFILES_FILE, {})
    clean: dict = {}
    for name, profile in result.items():
        if isinstance(profile, dict) and _is_valid_profile(profile):
            clean[name] = profile
        else:
            log_event("profile_invalid", "Skipped invalid model profile", {"name": name})
    set_cached("profiles", clean)
    return clean


def get_paid_profiles() -> dict:
    """Get only paid provider profiles."""
    return {k: v for k, v in load_profiles().items() if v.get("paid")}


def get_profile_choices() -> list[tuple[str, str, dict]]:
    """Get list of (display_name, model_id, profile) tuples."""
    profiles = load_profiles()
    choices = []
    for name, profile in profiles.items():
        if not _is_valid_profile(profile):
            continue
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
