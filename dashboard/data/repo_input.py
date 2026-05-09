"""
Repo Input
==========
Helpers for parsing what the user types into the Quick Start box. Accepts:

- Local Windows paths: ``C:\\path\\to\\repo``
- HTTPS git URLs:       ``https://github.com/owner/name`` (with or without .git)
- SSH git URLs:         ``git@github.com:owner/name.git``
- Already-cloned URLs sitting under ``workspaces/`` resolve back to the local
  path so a second Quick Start with the same URL re-uses the existing clone.

The dashboard never does ``git clone`` directly here; that responsibility lives
in scripts/magic-run.ps1 so the action is auditable from PowerShell logs. This
module only parses, validates, and computes the canonical local path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from dashboard.config import ROOT

WORKSPACES_DIR = ROOT / "workspaces"

# Tolerant URL matchers: pick up scheme + host even with trailing ``.git`` or query string.
_HTTPS_RE = re.compile(
    r"^(?P<scheme>https?)://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<name>[^/?#]+?)(?:\.git)?/?(?:[?#].*)?$",
    re.IGNORECASE,
)
_SSH_RE = re.compile(
    r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


@dataclass
class RepoTarget:
    kind: str            # "local" or "remote"
    raw: str             # exactly what the user typed
    local_path: str = "" # canonical absolute path (computed for both kinds)
    remote_url: str = "" # canonical clone URL when kind=="remote"
    owner: str = ""
    name: str = ""
    host: str = ""
    needs_clone: bool = False
    error: str = ""


def _slug(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in text).strip("-")
    return cleaned or "repo"


def parse(raw: str) -> RepoTarget:
    """Classify ``raw`` and compute the canonical local path."""
    text = (raw or "").strip().strip('"').strip("'")
    if not text:
        return RepoTarget(kind="local", raw=raw, error="Enter a path or repo URL.")

    # Local path? Treat anything with a Windows drive letter or starting with
    # / or \ as a path even before checking existence.
    if re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith(("\\", "/", "~")):
        local = Path(text).expanduser()
        try:
            absolute = local.resolve(strict=False)
        except Exception:
            absolute = local
        target = RepoTarget(
            kind="local",
            raw=raw,
            local_path=str(absolute),
            name=absolute.name,
        )
        if not absolute.exists():
            target.error = f"Path does not exist: {absolute}"
        elif not (absolute / ".git").exists():
            target.error = "Path exists but is not a git repository."
        return target

    https = _HTTPS_RE.match(text)
    ssh = _SSH_RE.match(text)
    match = https or ssh
    if not match:
        return RepoTarget(
            kind="local",
            raw=raw,
            error=(
                "Could not recognize this. Use a Windows path, an https://... "
                "git URL, or git@host:owner/name."
            ),
        )

    host = match.group("host").lower()
    owner = match.group("owner")
    name = match.group("name")
    if name.endswith(".git"):
        name = name[:-4]

    canonical_url = (
        f"https://{host}/{owner}/{name}.git"
        if https
        else f"git@{host}:{owner}/{name}.git"
    )

    folder = f"{_slug(owner)}-{_slug(name)}"
    local_path = (WORKSPACES_DIR / folder).resolve()

    return RepoTarget(
        kind="remote",
        raw=raw,
        local_path=str(local_path),
        remote_url=canonical_url,
        owner=owner,
        name=name,
        host=host,
        needs_clone=not (local_path / ".git").exists(),
    )


def workspace_for(owner: str, name: str) -> Path:
    return (WORKSPACES_DIR / f"{_slug(owner)}-{_slug(name)}").resolve()
