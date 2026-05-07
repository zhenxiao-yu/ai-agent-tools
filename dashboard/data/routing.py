"""
Routing Module
==============
Automatic model and execution recommendations for dashboard workflows.
"""
from dashboard.data.keys import key_present
from dashboard.data.profiles import load_profiles


TASK_PROFILES = {
    "quick_fix": {
        "label": "Quick Fix",
        "goal": "fastest safe edit loop",
        "prefers_local": True,
        "paid_profile": "deepseek_worker",
    },
    "code_review": {
        "label": "Code Review",
        "goal": "balanced reasoning and cost",
        "prefers_local": False,
        "paid_profile": "zai_reviewer",
    },
    "deep_planning": {
        "label": "Deep Planning",
        "goal": "long-context repo planning",
        "prefers_local": False,
        "paid_profile": "kimi_planner",
    },
    "parallel_projects": {
        "label": "Parallel Projects",
        "goal": "multiple small queues with predictable latency",
        "prefers_local": False,
        "paid_profile": "openrouter_gateway",
    },
    "scheduled_worker": {
        "label": "Scheduled Worker",
        "goal": "cheap unattended background pass",
        "prefers_local": True,
        "paid_profile": None,
    },
}


def get_ready_profiles() -> dict[str, dict]:
    """Return profiles that are actually usable right now."""
    ready: dict[str, dict] = {}
    for name, profile in load_profiles().items():
        if profile.get("paid"):
            if key_present(profile.get("apiKeyEnvVar")):
                ready[name] = profile
        else:
            ready[name] = profile
    return ready


def _default_local_model() -> str:
    profiles = load_profiles()
    profile = profiles.get("free_local") or profiles.get("fallback") or {}
    provider = profile.get("provider", "ollama")
    model = profile.get("model", "qwen2.5-coder:14b")
    return f"{provider}/{model}"


def _paid_model_id(profile: dict | None) -> str:
    if not profile:
        return ""
    return f"{profile.get('provider')}/{profile.get('model')}"


def recommend_execution_plan(
    task_key: str,
    active_projects: int,
    status: dict,
    allow_paid: bool = False,
) -> dict:
    """Recommend model routing, parallelism, and UX behavior."""
    task = TASK_PROFILES.get(task_key, TASK_PROFILES["quick_fix"])
    profiles = load_profiles()
    ready_profiles = get_ready_profiles()
    local_model = _default_local_model()
    paid_profile_name = task.get("paid_profile")
    paid_profile = ready_profiles.get(paid_profile_name) if allow_paid and paid_profile_name else None

    local_ready = bool(status.get("ollama"))
    models_text = status.get("models", "")
    local_loaded = "qwen2.5-coder:14b" in models_text or not models_text

    if task_key == "scheduled_worker":
        chosen = local_model
        route = "Local only"
        concurrency = 1
        lane_mode = "Single safe lane"
        reason = "Scheduled workers stay local, branch-based, and serial so they remain cheap and predictable."
    elif active_projects >= 3:
        if paid_profile:
            chosen = _paid_model_id(paid_profile)
            route = "Hybrid burst"
            concurrency = min(active_projects, 3)
            lane_mode = f"{concurrency} coordinated lanes"
            reason = "Multiple active projects will queue behind one local model, so paid routing reduces wait time for planning and review."
        else:
            chosen = local_model
            route = "Local queue"
            concurrency = 1
            lane_mode = "Single queued lane"
            reason = "One local model works best as a queue. More projects mean longer waits, so the dashboard should keep tasks small and serial."
    elif active_projects == 2:
        if paid_profile and not task.get("prefers_local"):
            chosen = _paid_model_id(paid_profile)
            route = "Split brain"
            concurrency = 2
            lane_mode = "Planner + worker lanes"
            reason = "Use a paid planner/reviewer lane while the local model keeps coding to avoid idle time."
        else:
            chosen = local_model
            route = "Local first"
            concurrency = 1
            lane_mode = "One active lane"
            reason = "Two projects are manageable locally if the work stays narrow and validation-first."
    else:
        if paid_profile and not task.get("prefers_local"):
            chosen = _paid_model_id(paid_profile)
            route = "Best fit"
            concurrency = 1
            lane_mode = "Focused lane"
            reason = "This task benefits more from reasoning depth than raw local throughput."
        else:
            chosen = local_model
            route = "Plug-and-play local"
            concurrency = 1
            lane_mode = "Focused lane"
            reason = "For one active project, local routing is simplest and keeps the workflow friction low."

    if not local_ready and not paid_profile:
        chosen = "No ready model"
        route = "Blocked"
        lane_mode = "Setup required"
        reason = "Neither Ollama nor a paid provider is ready. Start the local stack or configure one paid provider."

    speed_note = (
        "Local models share one machine. More simultaneous projects increase queue time and raise validation latency."
        if active_projects > 1
        else "One active project keeps local latency predictable and makes the UI feel much more responsive."
    )

    if paid_profile:
        fallback = f"Fallback to {local_model} if paid routing is disabled."
    else:
        fallback = "No paid fallback configured for this route."

    return {
        "task_label": task["label"],
        "chosen_model": chosen,
        "route_label": route,
        "lane_mode": lane_mode,
        "recommended_concurrency": concurrency,
        "reason": reason,
        "speed_note": speed_note,
        "fallback": fallback,
        "local_ready": local_ready,
        "local_loaded": local_loaded,
        "paid_ready_count": len([name for name, profile in ready_profiles.items() if profile.get("paid")]),
    }


def build_agent_flow(plan: dict) -> list[dict[str, str]]:
    """Describe the user-visible agent pipeline."""
    steps = [
        {
            "title": "Plan",
            "detail": f"Route task through {plan['chosen_model']} and keep the goal narrow.",
            "tone": "info",
        },
        {
            "title": "Run",
            "detail": f"Execute in {plan['lane_mode'].lower()} with concurrency {plan['recommended_concurrency']}.",
            "tone": "ready" if plan["recommended_concurrency"] <= 2 else "warn",
        },
        {
            "title": "Validate",
            "detail": "Run lint/build/test steps before surfacing the result.",
            "tone": "info",
        },
        {
            "title": "Review",
            "detail": "Present logs, diffs, and branch/report output for a human decision.",
            "tone": "ready",
        },
    ]
    return steps
