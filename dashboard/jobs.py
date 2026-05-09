"""
Async Jobs
==========
Submit, track, cancel, and tail long-running PowerShell jobs without blocking
Streamlit reruns. Each job has three sibling files in logs/jobs/:

- ``<id>.json`` — metadata (kind, label, args, repo, pid, status, exit_code)
- ``<id>.log``  — combined stdout/stderr captured by the wrapper script
- ``<id>.exit`` — single integer exit code, written by the wrapper when the
  inner script returns

The Python side never blocks on the subprocess: it spawns the wrapper detached,
records the PID, and reconciles status by checking the exit-code file and the
liveness of the recorded PID.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import signal
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dashboard.config import LOGS, ROOT, SCRIPTS

JOBS_DIR = LOGS / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

WRAPPER_SCRIPT = SCRIPTS / "_run-job.ps1"

ACTIVE_STATES = {"queued", "running"}


@dataclass
class Job:
    id: str
    kind: str
    label: str
    script: str
    args: list[str]
    repo: str = ""
    pid: int = 0
    submitted_at: str = ""
    started_at: str = ""
    ended_at: str = ""
    status: str = "queued"
    exit_code: Optional[int] = None
    log_path: str = ""

    def to_json(self) -> dict:
        return asdict(self)


def _meta_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _log_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.log"


def _exit_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.exit"


def _write_meta(job: Job) -> None:
    _meta_path(job.id).write_text(json.dumps(job.to_json(), indent=2), encoding="utf-8")


def _read_meta(job_id: str) -> Optional[Job]:
    path = _meta_path(job_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Job(**data)
    except Exception:
        return None


def _new_id(kind: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(3)
    safe_kind = "".join(ch if ch.isalnum() else "-" for ch in kind).strip("-") or "job"
    return f"{stamp}-{safe_kind}-{suffix}"


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _reconcile(job: Job) -> Job:
    """Refresh status by inspecting exit-marker file and PID liveness."""
    if job.status not in ACTIVE_STATES:
        return job

    exit_file = _exit_path(job.id)
    if exit_file.exists():
        try:
            code = int(exit_file.read_text(encoding="utf-8").strip())
        except Exception:
            code = 1
        job.exit_code = code
        job.status = "completed" if code == 0 else "failed"
        if not job.ended_at:
            job.ended_at = datetime.fromtimestamp(exit_file.stat().st_mtime).isoformat(timespec="seconds")
        _write_meta(job)
        return job

    if job.pid and not _is_alive(job.pid):
        job.status = "failed"
        if job.exit_code is None:
            job.exit_code = -1
        job.ended_at = _now_iso()
        _write_meta(job)

    return job


def submit(kind: str, label: str, script: str, args: list[str], repo: str = "") -> Job:
    """Spawn a wrapper subprocess that runs ``script`` with ``args`` detached."""
    job_id = _new_id(kind)
    log_path = _log_path(job_id)
    log_path.touch()

    job = Job(
        id=job_id,
        kind=kind,
        label=label,
        script=script,
        args=list(args),
        repo=repo,
        submitted_at=_now_iso(),
        log_path=str(log_path),
    )
    _write_meta(job)

    cmd: list[str] = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-NoProfile",
        "-File", str(WRAPPER_SCRIPT),
        "-JobId", job_id,
        "-ScriptPath", str((SCRIPTS / script).resolve()),
    ]
    if args:
        # Encode forwarded args as base64(JSON) to dodge any PowerShell
        # parameter-binding collisions on flags like ``-RepoPath``.
        encoded = base64.b64encode(json.dumps(list(args)).encode("utf-8")).decode("ascii")
        cmd.extend(["-ForwardJson", encoded])

    creationflags = 0
    if os.name == "nt":
        # CREATE_NO_WINDOW gives the child a hidden console (PowerShell needs
        # a console to initialize), and CREATE_NEW_PROCESS_GROUP detaches it
        # from the dashboard's Ctrl+C signal group so killing Streamlit does
        # not kill in-flight workers.
        creationflags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )

    job.pid = proc.pid
    job.status = "running"
    job.started_at = _now_iso()
    _write_meta(job)
    return job


def list_jobs(limit: int = 100) -> list[Job]:
    files = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    out: list[Job] = []
    for f in files:
        job = _read_meta(f.stem)
        if job:
            out.append(_reconcile(job))
    return out


def get(job_id: str) -> Optional[Job]:
    job = _read_meta(job_id)
    if not job:
        return None
    return _reconcile(job)


def cancel(job_id: str) -> bool:
    """Best-effort cancel: kill the wrapper process tree and mark cancelled."""
    job = _read_meta(job_id)
    if not job:
        return False
    if job.status not in ACTIVE_STATES:
        return False

    if job.pid and _is_alive(job.pid):
        try:
            if os.name == "nt":
                # Kill the wrapper plus any worker children (aider, npm, etc.)
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(job.pid)],
                    capture_output=True,
                    timeout=15,
                )
            else:
                os.kill(job.pid, signal.SIGTERM)
        except Exception:
            pass

    job.status = "cancelled"
    if job.exit_code is None:
        job.exit_code = -2
    job.ended_at = _now_iso()
    _write_meta(job)
    return True


def tail(job_id: str, max_chars: int = 12000) -> str:
    job = _read_meta(job_id)
    if not job:
        return ""
    log = Path(job.log_path) if job.log_path else _log_path(job_id)
    if not log.exists():
        return ""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return "...\n" + text[-max_chars:]
        return text
    except Exception:
        return ""


def cleanup_old(keep_last: int = 50) -> int:
    """Remove all but the most recent ``keep_last`` job records."""
    files = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for old in files[keep_last:]:
        job_id = old.stem
        job = _read_meta(job_id)
        if job and job.status in ACTIVE_STATES:
            continue  # never delete in-flight job records
        for ext in (".json", ".log", ".exit"):
            p = JOBS_DIR / f"{job_id}{ext}"
            if p.exists():
                try:
                    p.unlink()
                    if ext == ".json":
                        removed += 1
                except Exception:
                    pass
    return removed


def counts() -> dict:
    summary = {"queued": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
    for job in list_jobs(limit=200):
        summary[job.status] = summary.get(job.status, 0) + 1
    return summary
