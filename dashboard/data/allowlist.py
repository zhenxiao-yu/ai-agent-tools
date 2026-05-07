"""
Allowlist Module
================
Repository allowlist management.
"""
from pathlib import Path

from config import ALLOWLIST_FILE


def read_allowlist() -> list[str]:
    """Read repo allowlist."""
    ALLOWLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALLOWLIST_FILE.touch(exist_ok=True)
    return [
        line.strip()
        for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_allowlist(paths: list[str]) -> None:
    """Write repo allowlist preserving comments."""
    comments = []
    if ALLOWLIST_FILE.exists():
        comments = [
            line for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("#")
        ]

    clean = []
    for path in paths:
        if path and path not in clean:
            clean.append(path)

    ALLOWLIST_FILE.write_text("\n".join(comments + clean) + "\n", encoding="utf-8")


def add_repo(path: str) -> None:
    """Add a repo to allowlist."""
    repos = read_allowlist()
    if path not in repos:
        repos.append(path)
        write_allowlist(repos)


def remove_repo(path: str) -> None:
    """Remove a repo from allowlist."""
    repos = read_allowlist()
    if path in repos:
        repos.remove(path)
        write_allowlist(repos)


def validate_repo(path: str) -> tuple[bool, str]:
    """Validate repo path."""
    if not path:
        return False, "❌ Enter a repo path."

    repo = Path(path)
    if not repo.exists():
        return False, "❌ Path does not exist."
    if not (repo / ".git").exists():
        return False, "⚠️ Path exists, but it is not a Git repo."

    supported_markers = [
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "VERSION",
        "version.txt",
    ]
    if not any((repo / marker).exists() for marker in supported_markers):
        return False, (
            "⚠️ Git repo found, but no supported project file was detected. "
            "Expected one of: package.json, pyproject.toml, requirements.txt, "
            "Cargo.toml, go.mod, pom.xml, build.gradle, VERSION, or version.txt."
        )

    return True, "✅ Project is valid."
