"""
Services Module
===============
Service detection and status checking.
"""
import threading
import time
from typing import Any

from dashboard.cache import get_cached, set_cached
from dashboard.utils import run_cmd, ps_inline, test_http, log_event


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
    }


def _status_cache_name(include_optional: bool, include_model_details: bool) -> str:
    return f"service_status:{include_optional}:{include_model_details}"


def get_service_status_snapshot(
    include_optional: bool = False,
    include_model_details: bool = False,
) -> dict[str, Any]:
    """Return the last cached status immediately without triggering live checks."""
    cache_name = _status_cache_name(include_optional, include_model_details)
    cached = get_cached(cache_name, "service_status")
    return cached if cached else _empty_status()


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

    status: dict[str, Any] = _empty_status()

    results: dict[str, Any] = {}

    def timed_check(name: str, fn) -> None:
        started = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            results.setdefault("errors", []).append(f"{name}: {exc}")
            log_event("service_check_error", "Service check failed", {"name": name, "error": str(exc)})
        finally:
            results.setdefault("durations_ms", {})[name] = round((time.perf_counter() - started) * 1000, 1)

    def check_ollama() -> None:
        results["ollama"] = test_http("http://127.0.0.1:11434/api/tags", timeout=3)
        if results["ollama"] and include_model_details:
            code, models = run_cmd(["ollama", "list"], timeout=4)
            results["models"] = models if code == 0 else ""
            code, ps = run_cmd(["ollama", "ps"], timeout=4)
            results["ps"] = ps if code == 0 else ""

    def check_proxy() -> None:
        results["proxy"] = test_http(
            "http://127.0.0.1:8082/v1/models",
            {"x-api-key": "freecc"},
            timeout=3,
        )

    def check_cline() -> None:
        code, ext_out = ps_inline("code --list-extensions", timeout=8)
        results["cline"] = code == 0 and "saoudrizwan.claude-dev" in ext_out

    def check_aider() -> None:
        code, _ = ps_inline(
            'if ((Get-Command aider -ErrorAction SilentlyContinue) -or '
            '(Test-Path "$env:USERPROFILE\\.local\\bin\\aider.exe")) { exit 0 } else { exit 1 }',
            timeout=5,
        )
        results["aider"] = code == 0

    def check_docker() -> None:
        _, out = ps_inline(
            "if (Get-Command docker -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }",
            timeout=5,
        )
        results["docker"] = "yes" in out.lower()

    def check_openhands() -> None:
        results["openhands"] = test_http("http://127.0.0.1:3000", timeout=3)

    def check_playwright() -> None:
        code, pmcp_out = run_cmd(
            ["npm", "list", "-g", "@playwright/mcp", "--depth=0"],
            timeout=10,
        )
        results["playwright_mcp"] = code == 0 and "@playwright/mcp" in pmcp_out

    def check_github() -> None:
        code, _ = run_cmd(["gh", "auth", "status"], timeout=8)
        results["github"] = code == 0

    def check_scheduled() -> None:
        code, out = ps_inline(
            "Get-ScheduledTask -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TaskName",
            timeout=5,
        )
        results["scheduled"] = bool(out.strip())

    # Run checks in parallel
    threads = [
        threading.Thread(target=timed_check, args=("ollama", check_ollama), daemon=True),
        threading.Thread(target=timed_check, args=("proxy", check_proxy), daemon=True),
        threading.Thread(target=timed_check, args=("github", check_github), daemon=True),
        threading.Thread(target=timed_check, args=("scheduled", check_scheduled), daemon=True),
    ]

    if include_optional:
        threads.extend([
            threading.Thread(target=timed_check, args=("cline", check_cline), daemon=True),
            threading.Thread(target=timed_check, args=("aider", check_aider), daemon=True),
            threading.Thread(target=timed_check, args=("docker", check_docker), daemon=True),
            threading.Thread(target=timed_check, args=("openhands", check_openhands), daemon=True),
            threading.Thread(target=timed_check, args=("playwright_mcp", check_playwright), daemon=True),
        ])

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    status.update(results)
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
