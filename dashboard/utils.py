"""
Utilities Module
================
Common utility functions for the dashboard.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from config import SECRET_PATTERNS, LOGS, REPORTS, TEAM_REPORTS


def sanitize(text: str | None) -> str:
    """Sanitize sensitive information from text."""
    if not text:
        return ""
    safe = text
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            safe = pattern.sub(r"\1********", safe)
        else:
            safe = pattern.sub("********", safe)
    safe = __import__("re").sub(r"(?im)^.*\.env.*=.*$", "[hidden .env-like content]", safe)
    return safe


def run_cmd(args: list[str], timeout: int = 30, cwd: Path | None = None) -> tuple[int, str]:
    """Run a command with timeout and error handling."""
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, sanitize((proc.stdout or "") + (proc.stderr or ""))
    except subprocess.TimeoutExpired:
        return 124, f"⏱️ Timed out after {timeout}s: {' '.join(args)}"
    except Exception as exc:
        return 1, sanitize(str(exc))


def run_ps(script: str, *args: str, timeout: int = 240) -> tuple[int, str]:
    """Run a PowerShell script."""
    from config import SCRIPTS, ROOT

    return run_cmd(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / script), *args],
        timeout=timeout,
        cwd=ROOT,
    )


def ps_inline(command: str, timeout: int = 30) -> tuple[int, str]:
    """Run inline PowerShell command."""
    return run_cmd(["powershell", "-NoProfile", "-Command", command], timeout=timeout)


def test_http(url: str, headers: str | None = None, timeout: int = 5) -> bool:
    """Test HTTP endpoint availability."""
    header_part = f" -Headers {headers}" if headers else ""
    code, _ = ps_inline(
        f"Invoke-RestMethod '{url}'{header_part} -TimeoutSec {timeout} -ErrorAction SilentlyContinue | Out-Null",
        timeout=timeout + 2,
    )
    return code == 0


def latest_files(folder: Path, limit: int = 10, pattern: str = "*") -> list[Path]:
    """Get latest files from folder matching pattern."""
    try:
        if not folder.exists():
            return []
        files = [p for p in folder.glob(pattern) if p.is_file()]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    except Exception:
        return []


def file_preview(path: Path, max_chars: int = 1600) -> str:
    """Safely read file preview with sanitization."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")[:max_chars]
        return sanitize(content)
    except Exception as exc:
        return f"❌ Could not read file: {exc}"


def today_count(folder: Path, pattern: str) -> int:
    """Count files matching pattern created today."""
    today = datetime.now().date()
    return sum(
        1
        for p in latest_files(folder, 500, pattern)
        if datetime.fromtimestamp(p.stat().st_mtime).date() == today
    )


def load_json_file(path: Path, default: Any = None) -> Any:
    """Safely load JSON file."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default if default is not None else {}


def save_json_file(path: Path, data: Any) -> None:
    """Save data to JSON file."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def latest_matching(patterns: list[str]) -> Path | None:
    """Find latest file matching any pattern across logs and reports."""
    matches = []
    for pattern in patterns:
        matches.extend(latest_files(LOGS, 50, pattern))
        matches.extend(latest_files(REPORTS, 50, pattern))
        matches.extend(latest_files(TEAM_REPORTS, 50, pattern))
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0] if matches else None