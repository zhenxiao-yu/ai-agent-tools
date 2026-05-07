"""
Utilities Module
================
Common utility functions for the dashboard.
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from dashboard.config import SECRET_PATTERNS, LOGS, REPORTS, TEAM_REPORTS

DASHBOARD_EVENT_LOG = LOGS / "dashboard-events.log"


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
    safe = re.sub(r"(?im)^.*\.env.*=.*$", "[hidden .env-like content]", safe)
    return safe


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _ps_hashtable(headers: dict[str, str]) -> str:
    return "@{ " + "; ".join(f"{_ps_quote(k)}={_ps_quote(v)}" for k, v in headers.items()) + " }"


def log_event(kind: str, message: str, details: dict[str, Any] | None = None) -> None:
    """Append a structured dashboard event log entry."""
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "kind": kind,
            "message": sanitize(message),
            "details": sanitize(json.dumps(details or {}, ensure_ascii=True)),
        }
        with DASHBOARD_EVENT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


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
        output = sanitize((proc.stdout or "") + (proc.stderr or ""))
        if proc.returncode != 0:
            log_event("command_error", "Command returned non-zero exit code", {
                "args": args,
                "cwd": str(cwd) if cwd else "",
                "returncode": proc.returncode,
                "output": output[:1200],
            })
        return proc.returncode, output
    except subprocess.TimeoutExpired:
        output = f"⏱️ Timed out after {timeout}s: {' '.join(args)}"
        log_event("command_timeout", "Command timed out", {
            "args": args,
            "cwd": str(cwd) if cwd else "",
            "timeout": timeout,
        })
        return 124, output
    except Exception as exc:
        safe_exc = sanitize(str(exc))
        log_event("command_exception", "Command execution raised an exception", {
            "args": args,
            "cwd": str(cwd) if cwd else "",
            "error": safe_exc,
        })
        return 1, safe_exc


def run_ps(script: str, *args: str, timeout: int = 240) -> tuple[int, str]:
    """Run a PowerShell script."""
    from dashboard.config import SCRIPTS, ROOT

    return run_cmd(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / script), *args],
        timeout=timeout,
        cwd=ROOT,
    )


def ps_inline(command: str, timeout: int = 30) -> tuple[int, str]:
    """Run inline PowerShell command."""
    return run_cmd(["powershell", "-NoProfile", "-Command", command], timeout=timeout)


def test_http(url: str, headers: dict[str, str] | None = None, timeout: int = 5) -> bool:
    """Test HTTP endpoint availability."""
    header_part = f" -Headers {_ps_hashtable(headers)}" if headers else ""
    code, _ = ps_inline(
        f"Invoke-RestMethod {_ps_quote(url)}{header_part} -TimeoutSec {timeout} -ErrorAction SilentlyContinue | Out-Null",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def latest_matching(patterns: list[str]) -> Path | None:
    """Find latest file matching any pattern across logs and reports."""
    matches = []
    for pattern in patterns:
        matches.extend(latest_files(LOGS, 50, pattern))
        matches.extend(latest_files(REPORTS, 50, pattern))
        matches.extend(latest_files(TEAM_REPORTS, 50, pattern))
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0] if matches else None


def read_recent_log_lines(path: Path, limit: int = 40) -> list[str]:
    """Read the most recent lines from a text log file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return [sanitize(line) for line in lines[-limit:]]
    except Exception:
        return []


def recent_dashboard_events(limit: int = 30) -> list[str]:
    """Return recent structured dashboard events as compact strings."""
    if not DASHBOARD_EVENT_LOG.exists():
        return []

    lines = read_recent_log_lines(DASHBOARD_EVENT_LOG, limit=limit)
    formatted = []
    for line in lines:
        try:
            entry = json.loads(line)
            formatted.append(
                f"[{entry.get('timestamp', '?')}] {entry.get('kind', 'event')}: {entry.get('message', '')}"
            )
        except Exception:
            formatted.append(line)
    return formatted


def normalize_repo_path(path: str) -> str:
    """Normalize user-supplied repository paths."""
    return path.strip().strip('"').strip("'")


def validate_branch_name(name: str) -> tuple[bool, str]:
    """Validate a git branch name enough for dashboard settings."""
    value = (name or "").strip()
    if not value:
        return False, "Default branch cannot be empty."
    if value.startswith(("/", ".", "-")) or value.endswith(("/", ".")):
        return False, "Branch name has an invalid start or end character."
    if ".." in value or "@{" in value or "\\" in value or " " in value:
        return False, "Branch name contains invalid git ref characters."
    return True, ""
