"""
Services Module
===============
Service detection and status checking.
"""
import threading
from typing import Any

from cache import get_cached, set_cached
from config import CACHE_TTL
from utils import run_cmd, ps_inline, test_http


def get_service_status(force_refresh: bool = False) -> dict[str, Any]:
    """Get comprehensive service status with caching."""
    if not force_refresh:
        cached = get_cached("service_status", "service_status")
        if cached:
            return cached

    status: dict[str, Any] = {
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
    }

    results: dict[str, Any] = {}

    def check_ollama() -> None:
        results["ollama"] = test_http("http://127.0.0.1:11434/api/tags", timeout=3)
        if results["ollama"]:
            code, models = run_cmd(["ollama", "list"], timeout=8)
            results["models"] = models if code == 0 else ""
            code, ps = run_cmd(["ollama", "ps"], timeout=8)
            results["ps"] = ps if code == 0 else ""

    def check_proxy() -> None:
        results["proxy"] = test_http(
            "http://127.0.0.1:8082/v1/models",
            "@{ 'x-api-key'='freecc' }",
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
        threading.Thread(target=check_ollama),
        threading.Thread(target=check_proxy),
        threading.Thread(target=check_cline),
        threading.Thread(target=check_aider),
        threading.Thread(target=check_docker),
        threading.Thread(target=check_openhands),
        threading.Thread(target=check_playwright),
        threading.Thread(target=check_github),
        threading.Thread(target=check_scheduled),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    status.update(results)
    set_cached("service_status", status)
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