"""
Services Module
===============
Service detection and status checking.
"""
from datetime import datetime, timezone
import threading
import time
from typing import Any

from dashboard.cache import get_cached, set_cached
from dashboard.config import STATUS_BACKGROUND_REFRESH_COOLDOWN_SECONDS, STATUS_SNAPSHOT_MAX_AGE_SECONDS, STATUS_SNAPSHOTS
from dashboard.utils import load_json_file, log_event, ps_inline, run_cmd, save_json_file, test_http

_ACTIVE_REFRESHES: set[str] = set()
_ACTIVE_REFRESHES_LOCK = threading.Lock()
_LAST_REFRESH_REQUESTS: dict[str, float] = {}


def _empty_status() -> dict[str, Any]:
    return {
        "ollama": False,
        "proxy": False,
        "cline": False,
        "aider": False,
        "docker": False,
        "openhands": False,
        "playwright_mcp": False,
        "github": False,
        "scheduled": False,
        "models": "",
        "ps": "",
        "errors": [],
        "durations_ms": {},
        "snapshot_at": "",
        "snapshot_source": "none",
        "snapshot_age_seconds": None,
        "snapshot_ready": False,
    }


def _status_cache_name(include_optional: bool, include_model_details: bool) -> str:
    return f"service_status:{include_optional}:{include_model_details}"


def _snapshot_path(include_optional: bool, include_model_details: bool):
    return STATUS_SNAPSHOTS / f"service-status-{int(include_optional)}-{int(include_model_details)}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _snapshot_age_seconds(captured_at: str | None) -> int | None:
    captured_dt = _parse_timestamp(captured_at)
    if captured_dt is None:
        return None
    if captured_dt.tzinfo is None:
        captured_dt = captured_dt.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - captured_dt.astimezone(timezone.utc)
    return max(0, int(age.total_seconds()))


def _status_with_snapshot_meta(status: dict[str, Any], captured_at: str, source: str) -> dict[str, Any]:
    normalized = _empty_status()
    normalized.update(status or {})
    normalized["snapshot_at"] = captured_at or ""
    normalized["snapshot_source"] = source
    normalized["snapshot_age_seconds"] = _snapshot_age_seconds(captured_at)
    normalized["snapshot_ready"] = bool(captured_at)
    return normalized


def _read_persisted_snapshot(
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any] | None:
    payload = load_json_file(_snapshot_path(include_optional, include_model_details), default={})
    status = payload.get("status")
    captured_at = payload.get("captured_at", "")
    if not isinstance(status, dict) or not captured_at:
        return None
    return _status_with_snapshot_meta(status, captured_at, "disk")


def _write_persisted_snapshot(
    status: dict[str, Any],
    include_optional: bool = False,
    include_model_details: bool = False,
) -> None:
    persisted = {key: value for key, value in status.items() if not key.startswith("snapshot_")}
    save_json_file(
        _snapshot_path(include_optional, include_model_details),
        {
            "version": 1,
            "captured_at": status.get("snapshot_at", ""),
            "include_optional": include_optional,
            "include_model_details": include_model_details,
            "status": persisted,
        },
    )


def describe_service_status_snapshot(status: dict[str, Any]) -> str:
    """Return a compact freshness string for the UI."""
    if not status.get("snapshot_ready"):
        return "Checking machine status in the background."

    age = status.get("snapshot_age_seconds")
    source = status.get("snapshot_source", "snapshot")
    source_label = {
        "live": "live refresh",
        "disk": "saved snapshot",
        "session": "session cache",
    }.get(source, "snapshot")

    if age is None:
        return f"Showing {source_label}."
    if age < 5:
        age_text = "just now"
    elif age < 60:
        age_text = f"{age}s ago"
    elif age < 3600:
        age_text = f"{max(1, age // 60)}m ago"
    else:
        age_text = f"{max(1, age // 3600)}h ago"
    return f"Showing {source_label} from {age_text}."


def _probe_service_status(
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any]:
    status: dict[str, Any] = _empty_status()
    results: dict[str, Any] = {}
    results_lock = threading.Lock()

    def set_result(key: str, value: Any) -> None:
        with results_lock:
            results[key] = value

    def append_error(message: str) -> None:
        with results_lock:
            results.setdefault("errors", []).append(message)

    def set_duration(name: str, duration_ms: float) -> None:
        with results_lock:
            results.setdefault("durations_ms", {})[name] = round(duration_ms, 1)

    def timed_check(name: str, fn) -> None:
        started = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            append_error(f"{name}: {exc}")
            log_event("service_check_error", "Service check failed", {"name": name, "error": str(exc)})
        finally:
            set_duration(name, (time.perf_counter() - started) * 1000)

    def check_ollama() -> None:
        ollama_ready = test_http("http://127.0.0.1:11434/api/tags", timeout=3)
        set_result("ollama", ollama_ready)
        if ollama_ready and include_model_details:
            code, models = run_cmd(["ollama", "list"], timeout=4)
            set_result("models", models if code == 0 else "")
            code, ps = run_cmd(["ollama", "ps"], timeout=4)
            set_result("ps", ps if code == 0 else "")

    def check_proxy() -> None:
        set_result(
            "proxy",
            test_http(
                "http://127.0.0.1:8082/v1/models",
                {"x-api-key": "freecc"},
                timeout=3,
            ),
        )

    def check_cline() -> None:
        code, ext_out = ps_inline("code --list-extensions", timeout=8)
        set_result("cline", code == 0 and "saoudrizwan.claude-dev" in ext_out)

    def check_aider() -> None:
        code, _ = ps_inline(
            'if ((Get-Command aider -ErrorAction SilentlyContinue) -or '
            '(Test-Path "$env:USERPROFILE\\.local\\bin\\aider.exe")) { exit 0 } else { exit 1 }',
            timeout=5,
        )
        set_result("aider", code == 0)

    def check_docker() -> None:
        _, out = ps_inline(
            "if (Get-Command docker -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }",
            timeout=5,
        )
        set_result("docker", "yes" in out.lower())

    def check_openhands() -> None:
        set_result("openhands", test_http("http://127.0.0.1:3000", timeout=3))

    def check_playwright() -> None:
        code, pmcp_out = run_cmd(
            ["npm", "list", "-g", "@playwright/mcp", "--depth=0"],
            timeout=10,
        )
        set_result("playwright_mcp", code == 0 and "@playwright/mcp" in pmcp_out)

    def check_github() -> None:
        code, _ = run_cmd(["gh", "auth", "status"], timeout=8)
        set_result("github", code == 0)

    def check_scheduled() -> None:
        code, out = ps_inline(
            "Get-ScheduledTask -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TaskName",
            timeout=5,
        )
        set_result("scheduled", code == 0 and bool(out.strip()))

    checks = [
        ("ollama", check_ollama),
        ("proxy", check_proxy),
        ("github", check_github),
        ("scheduled", check_scheduled),
    ]

    if include_optional:
        checks.extend([
            ("cline", check_cline),
            ("aider", check_aider),
            ("docker", check_docker),
            ("openhands", check_openhands),
            ("playwright_mcp", check_playwright),
        ])

    threads = [
        threading.Thread(target=timed_check, args=(name, fn), daemon=True)
        for name, fn in checks
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    status.update(results)
    return _status_with_snapshot_meta(status, _now_iso(), "live")


def refresh_service_status_snapshot(
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any]:
    """Run live checks and persist the result for future instant loads."""
    status = _probe_service_status(
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    _write_persisted_snapshot(
        status,
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    return status


def _background_refresh_worker(include_optional: bool, include_model_details: bool) -> None:
    cache_name = _status_cache_name(include_optional, include_model_details)
    try:
        refresh_service_status_snapshot(
            include_optional=include_optional,
            include_model_details=include_model_details,
        )
        log_event(
            "service_snapshot_refreshed",
            "Background service snapshot refreshed",
            {
                "include_optional": include_optional,
                "include_model_details": include_model_details,
            },
        )
    finally:
        with _ACTIVE_REFRESHES_LOCK:
            _ACTIVE_REFRESHES.discard(cache_name)


def ensure_service_status_snapshot_fresh(
    include_optional: bool = False,
    include_model_details: bool = False,
    max_age_seconds: int = STATUS_SNAPSHOT_MAX_AGE_SECONDS,
) -> bool:
    """Queue a background refresh when the saved snapshot is missing or stale."""
    status = _read_persisted_snapshot(
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    if status and status.get("snapshot_age_seconds") is not None:
        if status["snapshot_age_seconds"] <= max_age_seconds:
            return False

    cache_name = _status_cache_name(include_optional, include_model_details)
    with _ACTIVE_REFRESHES_LOCK:
        if cache_name in _ACTIVE_REFRESHES:
            return False
        last_requested = _LAST_REFRESH_REQUESTS.get(cache_name, 0.0)
        if time.time() - last_requested < STATUS_BACKGROUND_REFRESH_COOLDOWN_SECONDS:
            return False
        _ACTIVE_REFRESHES.add(cache_name)
        _LAST_REFRESH_REQUESTS[cache_name] = time.time()

    thread = threading.Thread(
        target=_background_refresh_worker,
        args=(include_optional, include_model_details),
        daemon=True,
        name=f"service-refresh-{cache_name}",
    )
    thread.start()
    return True


def get_service_status_snapshot(
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any]:
    """Return the last cached status immediately without triggering live checks."""
    cache_name = _status_cache_name(include_optional, include_model_details)
    cached = get_cached(cache_name, "service_status")
    if cached:
        return _status_with_snapshot_meta(
            {key: value for key, value in cached.items() if not key.startswith("snapshot_")},
            cached.get("snapshot_at", ""),
            "session",
        )

    persisted = _read_persisted_snapshot(
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    if persisted:
        set_cached(cache_name, persisted)
        return persisted
    return _empty_status()


def get_service_status(
    force_refresh: bool = False,
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any]:
    """Get comprehensive service status with caching."""
    cache_name = _status_cache_name(include_optional, include_model_details)
    if not force_refresh:
        cached = get_cached(cache_name, "service_status")
        if cached:
            return cached
        persisted = _read_persisted_snapshot(
            include_optional=include_optional,
            include_model_details=include_model_details,
        )
        if persisted:
            set_cached(cache_name, persisted)
            return persisted

    status = refresh_service_status_snapshot(
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    set_cached(cache_name, status)
    return status


def scheduled_info() -> tuple[bool, str]:
    """Get scheduled task info."""
    code, out = ps_inline(
        "Get-ScheduledTask -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | "
        "Select-Object TaskName,State | Format-List; "
        "Get-ScheduledTaskInfo -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | "
        "Format-List LastRunTime,NextRunTime,LastTaskResult",
        timeout=12,
    )
    return bool(out.strip()), out
