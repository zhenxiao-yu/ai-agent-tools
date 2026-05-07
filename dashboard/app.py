import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st


ROOT = Path(r"C:\ai-agent-tools")
SCRIPTS = ROOT / "scripts"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
TEAM_REPORTS = ROOT / "team" / "reports"
CONFIGS = ROOT / "configs"
ALLOWLIST = CONFIGS / "repo-allowlist.txt"
PROFILES = CONFIGS / "model-profiles.json"
SETTINGS = CONFIGS / "dashboard-settings.json"

DEFAULT_SETTINGS = {
    "defaultModel": "ollama/qwen2.5-coder:14b",
    "defaultBaseBranch": "main",
    "defaultIntervalHours": 2,
    "safetyMode": True,
    "advancedMode": False,
}

SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_\-]{12,})"),
    re.compile(r"(gho_[A-Za-z0-9_\-]{12,})"),
    re.compile(r"((?:API_KEY|TOKEN|SECRET|PASSWORD)\s*[=:]\s*)[^\s]+", re.I),
    re.compile(r"([A-Za-z0-9_\-]{32,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,})"),
]


st.set_page_config(page_title="Local AI Mission Control", layout="wide", initial_sidebar_state="expanded")


def sanitize(text: str) -> str:
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


def run_cmd(args: list[str], timeout: int = 30, cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, sanitize((proc.stdout or "") + (proc.stderr or ""))
    except subprocess.TimeoutExpired:
        return 124, f"Timed out after {timeout}s: {' '.join(args)}"
    except Exception as exc:
        return 1, sanitize(str(exc))


def run_ps(script: str, *args: str, timeout: int = 240) -> tuple[int, str]:
    return run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / script), *args], timeout=timeout, cwd=ROOT)


def ps_inline(command: str, timeout: int = 30) -> tuple[int, str]:
    return run_cmd(["powershell", "-NoProfile", "-Command", command], timeout=timeout)


def test_http(url: str, headers: str = "") -> bool:
    header_part = f" -Headers {headers}" if headers else ""
    code, _ = ps_inline(f"Invoke-RestMethod '{url}'{header_part} | Out-Null", timeout=5)
    return code == 0


def latest_files(folder: Path, limit: int = 10, pattern: str = "*") -> list[Path]:
    try:
        if not folder.exists():
            return []
        return sorted([p for p in folder.glob(pattern) if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    except Exception:
        return []


def file_preview(path: Path, max_chars: int = 1600) -> str:
    try:
        return sanitize(path.read_text(encoding="utf-8", errors="replace")[:max_chars])
    except Exception as exc:
        return f"Could not read file: {exc}"


def today_count(folder: Path, pattern: str) -> int:
    today = datetime.now().date()
    return sum(1 for p in latest_files(folder, 500, pattern) if datetime.fromtimestamp(p.stat().st_mtime).date() == today)


def read_allowlist() -> list[str]:
    ALLOWLIST.parent.mkdir(parents=True, exist_ok=True)
    ALLOWLIST.touch(exist_ok=True)
    return [line.strip() for line in ALLOWLIST.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]


def write_allowlist(paths: list[str]) -> None:
    comments = [line for line in ALLOWLIST.read_text(encoding="utf-8").splitlines() if line.strip().startswith("#")] if ALLOWLIST.exists() else []
    clean = []
    for path in paths:
        if path and path not in clean:
            clean.append(path)
    ALLOWLIST.write_text("\n".join(comments + clean) + "\n", encoding="utf-8")


def load_settings() -> dict:
    if not SETTINGS.exists():
        SETTINGS.write_text(json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        return {**DEFAULT_SETTINGS, **data}
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    SETTINGS.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def load_profiles() -> dict:
    try:
        return json.loads(PROFILES.read_text(encoding="utf-8")) if PROFILES.exists() else {}
    except Exception:
        return {}


def key_present(env_var: str | None) -> bool:
    if not env_var:
        return False
    code, out = ps_inline(f"if ([Environment]::GetEnvironmentVariable('{env_var}','Process') -or [Environment]::GetEnvironmentVariable('{env_var}','User') -or [Environment]::GetEnvironmentVariable('{env_var}','Machine')) {{ 'yes' }} else {{ 'no' }}", timeout=5)
    return code == 0 and "yes" in out.lower()


def chip(label: str, tone: str = "muted") -> str:
    return f'<span class="chip chip-{tone}">{label}</span>'


def section_intro(title: str, text: str, chips: list[tuple[str, str]] | None = None) -> None:
    chip_html = " ".join(chip(label, tone) for label, tone in (chips or []))
    st.markdown(f'<div class="page-head"><h2>{title}</h2><p>{text}</p><div>{chip_html}</div></div>', unsafe_allow_html=True)


def card(title: str, value: str, detail: str = "", tone: str = "info") -> None:
    st.markdown(
        f'<div class="mc-card"><div class="card-kicker">{title}</div><div class="card-value card-{tone}">{value}</div><div class="card-detail">{detail}</div></div>',
        unsafe_allow_html=True,
    )


def action_result(label: str, code: int, out: str) -> None:
    if code == 0:
        st.success(f"{label}: finished")
    else:
        st.error(f"{label}: exit code {code}")
    with st.expander("Command output", expanded=code != 0):
        st.code(out or "(no output)")


def project_status(path: str) -> dict:
    repo = Path(path)
    info = {
        "name": repo.name or path,
        "path": path,
        "exists": repo.exists(),
        "git": False,
        "package": False,
        "branch": "Unknown",
        "dirty": "Unknown",
        "framework": "Unknown",
        "packageManager": "npm",
        "scripts": [],
        "aiBranches": [],
        "latestReport": "",
        "latestLog": "",
        "risk": "Unknown",
        "nextAction": "Run health scan",
        "why": "Start with a no-edit scan so the system understands the repo.",
    }
    if not repo.exists():
        info.update({"risk": "Blocked", "nextAction": "Remove or fix path", "why": "The path no longer exists."})
        return info
    info["git"] = (repo / ".git").exists()
    info["package"] = (repo / "package.json").exists()
    if not info["git"]:
        info.update({"risk": "Blocked", "nextAction": "Choose a Git repo", "why": "Worker mode requires Git branches."})
        return info
    code, out = run_cmd(["git", "-C", str(repo), "branch", "--show-current"], timeout=8)
    if code == 0 and out.strip():
        info["branch"] = out.strip()
    code, out = run_cmd(["git", "-C", str(repo), "status", "--porcelain"], timeout=8)
    if code == 0:
        info["dirty"] = "Dirty" if out.strip() else "Clean"
    code, out = run_cmd(["git", "-C", str(repo), "branch", "--list", "ai/*", "--sort=-committerdate"], timeout=8)
    if code == 0:
        info["aiBranches"] = [line.strip().lstrip("* ").strip() for line in out.splitlines() if line.strip()][:5]
    package = repo / "package.json"
    if package.exists():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))
            if "next" in deps:
                info["framework"] = "Next.js"
            elif "vite" in deps:
                info["framework"] = "Vite"
            elif "vue" in deps:
                info["framework"] = "Vue"
            elif "react" in deps:
                info["framework"] = "React"
            elif "express" in deps:
                info["framework"] = "Express"
            scripts = data.get("scripts", {})
            info["scripts"] = list(scripts.keys())
        except Exception:
            info["framework"] = "package.json parse issue"
    if (repo / "pnpm-lock.yaml").exists():
        info["packageManager"] = "pnpm"
    elif (repo / "yarn.lock").exists():
        info["packageManager"] = "yarn"
    elif (repo / "package-lock.json").exists():
        info["packageManager"] = "npm"
    repo_name = repo.name
    report = latest_files(REPORTS, 1, f"*{repo_name}*.md")
    log = latest_files(LOGS, 1, f"*{repo_name}*.log")
    info["latestReport"] = str(report[0]) if report else ""
    info["latestLog"] = str(log[0]) if log else ""
    if info["dirty"] == "Dirty":
        info.update({"risk": "Needs Review", "nextAction": "Morning review", "why": "There are uncommitted changes. Review before running workers."})
    elif not info["package"]:
        info.update({"risk": "Blocked", "nextAction": "No web worker", "why": "No package.json was found."})
    elif info["aiBranches"]:
        info.update({"risk": "Needs Review", "nextAction": "Review latest AI branch", "why": "An AI branch exists. Review diff before more automation."})
    else:
        info.update({"risk": "Low", "nextAction": "Run dry-run", "why": "Repo is clean and ready for a no-edit worker simulation."})
    return info


def run_list() -> list[dict]:
    items = []
    for folder, kind in [(LOGS, "log"), (REPORTS, "report"), (TEAM_REPORTS, "review")]:
        for path in latest_files(folder, 200, "*"):
            name = path.name
            stamp = datetime.fromtimestamp(path.stat().st_mtime)
            status = "Needs Review" if "worker" in name or "review" in name else "Info"
            if "dry-run" in name:
                action = "Dry Run"
            elif "worker" in name:
                action = "Worker"
            elif "validation" in name:
                action = "Validation"
            elif "provider" in name:
                action = "Provider"
            elif "review" in name:
                action = "Review"
            else:
                action = "System"
            items.append({"time": stamp, "kind": kind, "action": action, "status": status, "file": str(path), "name": name})
    return sorted(items, key=lambda x: x["time"], reverse=True)


def scheduled_info() -> tuple[bool, str]:
    code, out = ps_inline("Get-ScheduledTask -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-List; Get-ScheduledTaskInfo -TaskName 'Local Web AI Worker' -ErrorAction SilentlyContinue | Format-List LastRunTime,NextRunTime,LastTaskResult", timeout=12)
    return bool(out.strip()), out


def validate_project_path(path: str) -> tuple[bool, str]:
    if not path:
        return False, "Enter a repo path."
    repo = Path(path)
    if not repo.exists():
        return False, "Path does not exist."
    if not (repo / ".git").exists():
        return False, "Path exists, but it is not a Git repo."
    if not (repo / "package.json").exists():
        return False, "Git repo found, but package.json is missing."
    return True, "Project is valid."


def render_repo_actions(path: str, branch: str, prefix: str) -> None:
    cols = st.columns(4)
    actions = [
        ("Health Scan", "repo-health-scan.ps1", [], "No edits"),
        ("Audit", "audit-web-repo.ps1", [], "No edits"),
        ("Dry Run", "run-web-ai-worker.ps1", ["-BaseBranch", branch or "main", "-DryRun"], "No edits"),
        ("Reviewer", "run-ai-reviewer.ps1", [], "No edits"),
        ("Morning Review", "morning-review.ps1", [], "No edits"),
        ("Validation", "repo-validation-runner.ps1", [], "Runs checks"),
        ("GitHub Pipelines", "check-github-pipelines.ps1", [], "No edits"),
    ]
    for i, (label, script, extra, hint) in enumerate(actions):
        with cols[i % 4]:
            if st.button(f"{label}", key=f"{prefix}-{label}-{path}", help=hint):
                code, out = run_ps(script, "-RepoPath", path, *extra, timeout=900)
                action_result(label, code, out)
    if st.button("Open in VS Code", key=f"{prefix}-vscode-{path}"):
        subprocess.Popen(["code", path])


st.markdown(
    """
    <style>
    :root {
      --bg: #05070b;
      --panel: #0b1117;
      --panel2: #0f1720;
      --line: #20303c;
      --green: #42f59b;
      --cyan: #38d8ff;
      --yellow: #f7c948;
      --red: #ff5a6a;
      --muted: #8ca3b5;
      --text: #e6f1ff;
    }
    .stApp { background: radial-gradient(circle at top left, #0b2a2a 0, #05070b 34rem); color: var(--text); }
    section[data-testid="stSidebar"] { background: #05070b; border-right: 1px solid var(--line); }
    h1, h2, h3 { letter-spacing: 0; }
    .hero {
      border: 1px solid #1d3e48;
      background: linear-gradient(135deg, rgba(11, 36, 36, .94), rgba(5, 8, 14, .96));
      border-radius: 8px;
      padding: 1.4rem 1.6rem;
      margin-bottom: 1rem;
      box-shadow: 0 0 32px rgba(56,216,255,.08);
    }
    .hero h1 { margin: 0; font-size: 2.2rem; color: #e9fbff; }
    .hero p { color: #b8c7d4; margin: .4rem 0 0; font-size: 1rem; }
    .top-banner {
      border: 1px solid rgba(66,245,155,.3);
      background: rgba(12, 28, 22, .78);
      border-radius: 8px;
      padding: .65rem .85rem;
      color: #c9ffe2;
      margin-bottom: 1rem;
    }
    .page-head {
      border: 1px solid var(--line);
      background: rgba(10, 18, 25, .82);
      border-radius: 8px;
      padding: 1rem 1.1rem;
      margin-bottom: 1rem;
    }
    .page-head h2 { margin: 0 0 .25rem; color: #dffcff; }
    .page-head p { color: #aebdca; margin: 0 0 .65rem; }
    .mc-card {
      min-height: 116px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #0d151d, #081017);
      border-radius: 8px;
      padding: .95rem;
      margin-bottom: .8rem;
    }
    .card-kicker { color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .06rem; }
    .card-value { font-size: 1.35rem; font-weight: 700; margin-top: .25rem; }
    .card-detail { color: #9fb3c5; font-size: .86rem; margin-top: .25rem; }
    .card-ready { color: var(--green); }
    .card-warn { color: var(--yellow); }
    .card-danger { color: var(--red); }
    .card-info { color: var(--cyan); }
    .chip {
      display: inline-block;
      border-radius: 999px;
      padding: .18rem .55rem;
      margin: 0 .25rem .25rem 0;
      font-size: .74rem;
      border: 1px solid var(--line);
      color: #c5d7e6;
      background: #101923;
    }
    .chip-ready { color: #baffd5; border-color: rgba(66,245,155,.4); background: rgba(66,245,155,.08); }
    .chip-warn { color: #ffe8a3; border-color: rgba(247,201,72,.45); background: rgba(247,201,72,.09); }
    .chip-danger { color: #ffb5bd; border-color: rgba(255,90,106,.45); background: rgba(255,90,106,.09); }
    .chip-info { color: #b8f0ff; border-color: rgba(56,216,255,.45); background: rgba(56,216,255,.09); }
    .chip-muted { color: #bac8d4; border-color: #253240; background: #111922; }
    div[data-testid="stButton"] button {
      border-radius: 8px;
      border: 1px solid #265466;
      background: #0d1a22;
      color: #dffcff;
    }
    div[data-testid="stButton"] button:hover {
      border-color: var(--cyan);
      color: white;
    }
    code, pre { font-family: "Cascadia Code", Consolas, monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

settings = load_settings()

st.markdown(
    """
    <div class="hero">
      <h1>LOCAL AI MISSION CONTROL</h1>
      <p>Free local coding agents for your repos, with safety gates, logs, reviews, and controlled multi-project vibe coding.</p>
    </div>
    <div class="top-banner">Mode: Free Local by default · Paid providers manual only · Scheduled workers local-only · No auto-push · No auto-commit</div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Navigation")
    page = st.selectbox(
        "Go to",
        [
            "Home",
            "Fix Center",
            "Tools / Integrations",
            "Workflow Wizard",
            "Projects",
            "Vibe Code",
            "Runs",
            "Morning Review",
            "Scheduler",
            "Models",
            "Providers",
            "Logs & Reports",
            "VS Code",
            "Settings",
            "Help",
        ],
        key="nav_page",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(chip("Free Local", "ready") + chip("Paid Manual", "warn") + chip("No Auto-Push", "info"), unsafe_allow_html=True)
    st.caption("Safety mode is ON by default. Risky actions require confirmation.")


def page_home() -> None:
    section_intro("Home", "What is running, whether it is safe, and what to do next.", [("Free Local Mode", "ready"), ("Stable", "info")])
    ollama = test_http("http://127.0.0.1:11434/api/tags")
    proxy = test_http("http://127.0.0.1:8082/v1/models", "@{ 'x-api-key'='freecc' }")
    code, models = run_cmd(["ollama", "list"], timeout=10)
    code_ps, ps = run_cmd(["ollama", "ps"], timeout=10)
    code_gh, _ = run_cmd(["gh", "auth", "status"], timeout=12)
    scheduled, sched_out = scheduled_info()
    repos = read_allowlist()
    runs_today = today_count(LOGS, "web-ai-*.log") + today_count(LOGS, "paid-web-ai-worker-*.log")
    failures_today = 0
    for p in latest_files(LOGS, 80, "*.log"):
        if datetime.fromtimestamp(p.stat().st_mtime).date() == datetime.now().date() and re.search(r"\b(ERROR|FAIL|failed)\b", file_preview(p, 2500), re.I):
            failures_today += 1
    cols = st.columns(4)
    with cols[0]:
        card("Free Local AI", "Ready" if ollama else "Not Ready", "Ollama API status", "ready" if ollama else "danger")
    with cols[1]:
        card("Default Model", "Available" if "qwen2.5-coder:14b" in models else "Missing", "qwen2.5-coder:14b", "ready" if "qwen2.5-coder:14b" in models else "danger")
    with cols[2]:
        card("GPU", "Active" if "GPU" in ps else "Unknown", "From ollama ps", "ready" if "GPU" in ps else "warn")
    with cols[3]:
        card("Proxy", "Online" if proxy else "Offline", "free-claude-code", "ready" if proxy else "warn")
    cols = st.columns(4)
    with cols[0]:
        card("Dashboard", "Online", "http://127.0.0.1:8501", "ready")
    with cols[1]:
        card("GitHub", "Authenticated" if code_gh == 0 else "Not Connected", "gh auth status", "ready" if code_gh == 0 else "warn")
    with cols[2]:
        card("Scheduled Worker", "Enabled" if scheduled else "Disabled", "Local-only scheduler", "warn" if scheduled else "muted")
    with cols[3]:
        card("Projects", str(len(repos)), "Allowlisted repos", "info")
    c1, c2 = st.columns(2)
    with c1:
        card("Runs Today", str(runs_today), "Worker and dry-run logs", "info")
    with c2:
        card("Failures Today", str(failures_today), "Logs containing fail/error", "danger" if failures_today else "ready")
    if not repos:
        next_step = "Add your first project"
        why = "The system needs one explicit repo path. It never scans your whole drive."
    elif any(project_status(p)["dirty"] == "Dirty" for p in repos if Path(p).exists()):
        next_step = "Review latest AI branch"
        why = "At least one project has uncommitted changes. Review before running more automation."
    else:
        next_step = "Run a dry-run before editing"
        why = "Dry-run checks repo safety and validation commands without creating a branch."
    st.markdown(f"### Recommended Next Step\n**{next_step}**\n\n{why}")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Add Project"):
            st.session_state["nav_hint"] = "Projects"
            st.info("Open the Projects page and use Add Project.")
    with c2:
        if st.button("Open Dashboard Health Check"):
            code, out = run_ps("health-local-ai-stack.ps1", timeout=120)
            action_result("Health check", code, out)
    with c3:
        if st.button("Start Free Local Stack"):
            code, out = run_ps("start-local-model-stack.ps1", timeout=240)
            action_result("Start local stack", code, out)
    with st.expander("Raw scheduler status"):
        st.code(sched_out or "Scheduled worker not installed.")
    if not ollama or not proxy or failures_today:
        st.warning("Something needs attention. Open Fix Center for safe recovery actions.")


def latest_matching(patterns: list[str]) -> Path | None:
    matches = []
    for pattern in patterns:
        matches.extend(latest_files(LOGS, 50, pattern))
        matches.extend(latest_files(REPORTS, 50, pattern))
        matches.extend(latest_files(TEAM_REPORTS, 50, pattern))
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0] if matches else None


def issue_card(
    key: str,
    status: str,
    severity: str,
    problem: str,
    why: str,
    fix: str,
    manual: str,
    safety: str,
    auto_script: str | None = None,
    auto_args: list[str] | None = None,
    log_path: Path | None = None,
    report_path: Path | None = None,
    repo_path: str | None = None,
    emergency: bool = False,
    confirm_text: str | None = None,
) -> None:
    tone = {"Low": "info", "Medium": "warn", "High": "danger", "Critical": "danger"}.get(severity, "info")
    st.markdown(f"### {problem} {chip(status, tone)} {chip(severity, tone)}", unsafe_allow_html=True)
    st.write(f"**Why it matters:** {why}")
    st.write(f"**Recommended fix:** {fix}")
    st.info(f"Safety note: {safety}")
    st.code(manual)
    cols = st.columns(4)
    with cols[0]:
        if auto_script:
            ok_to_run = True
            if confirm_text:
                ok_to_run = st.checkbox(confirm_text, key=f"confirm-{key}")
            if st.button("Fix Automatically", key=f"fix-{key}", disabled=not ok_to_run):
                code, out = run_ps(auto_script, *(auto_args or []), timeout=600)
                action_result(problem, code, out)
        else:
            st.button("Fix Automatically", key=f"fix-disabled-{key}", disabled=True, help="Manual-only issue.")
    with cols[1]:
        if st.button("Retry Check", key=f"retry-{key}"):
            st.rerun()
    with cols[2]:
        if log_path and st.button("Open Log", key=f"log-{key}"):
            os.startfile(str(log_path))
        elif report_path and st.button("Open Report", key=f"report-{key}"):
            os.startfile(str(report_path))
    with cols[3]:
        if repo_path and st.button("Open Repo in VS Code", key=f"repo-{key}"):
            subprocess.Popen(["code", repo_path])
        elif emergency and st.button("Emergency Stop", key=f"stop-{key}"):
            code, out = run_ps("remove-scheduled-web-worker.ps1", timeout=120)
            action_result("Emergency stop", code, out)
    with st.expander("View manual steps"):
        st.markdown(fix)
        st.code(manual)
    if log_path:
        with st.expander("Log preview"):
            st.code(file_preview(log_path, 5000))
    if report_path:
        with st.expander("Report preview"):
            st.code(file_preview(report_path, 5000))


def collect_issues() -> list[dict]:
    issues = []
    ollama = test_http("http://127.0.0.1:11434/api/tags")
    proxy = test_http("http://127.0.0.1:8082/v1/models", "@{ 'x-api-key'='freecc' }")
    code_models, models = run_cmd(["ollama", "list"], timeout=10)
    if not ollama:
        issues.append(dict(key="ollama-offline", status="Fixable", severity="High", problem="Ollama offline", why="Local model server is not responding, so local AI workers cannot run.", fix="Start the local model stack.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\start-local-model-stack.ps1", safety="This starts/checks Ollama only. It does not touch repos, commit, push, or use paid APIs.", auto_script="start-local-model-stack.ps1"))
    elif "qwen2.5-coder:14b" not in models:
        issues.append(dict(key="model-missing", status="Needs Review", severity="High", problem="Default model missing", why="The worker default model qwen2.5-coder:14b is not installed.", fix="Pull the model after confirming disk/time cost.", manual="ollama pull qwen2.5-coder:14b", safety="This downloads a local model only. It does not touch repos or call paid APIs.", confirm_text="I approve downloading qwen2.5-coder:14b."))
    if not proxy:
        issues.append(dict(key="proxy-offline", status="Fixable", severity="Medium", problem="free-claude-code proxy offline", why="Claude Code-compatible local mode will not work while the proxy is offline.", fix="Start the local proxy.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\start-free-claude-code-proxy.ps1", safety="This starts a localhost proxy only. It does not use paid APIs.", auto_script="start-free-claude-code-proxy.ps1"))
    if not test_http("http://127.0.0.1:8501"):
        issues.append(dict(key="dashboard-offline", status="Fixable", severity="Medium", problem="Dashboard not opening", why="The control center is not responding on port 8501.", fix="Start the dashboard and inspect dashboard-start.log if needed.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\start-dashboard.ps1", safety="This starts Streamlit only.", auto_script="start-dashboard.ps1", log_path=LOGS / "dashboard-start.log"))
    code_gh, gh_out = run_cmd(["gh", "auth", "status"], timeout=12)
    if code_gh != 0:
        issues.append(dict(key="gh-auth", status="Manual Only", severity="Medium", problem="GitHub CLI not authenticated", why="GitHub pipeline checks need gh auth.", fix="Run gh auth login and choose GitHub.com, HTTPS, Login with browser.", manual="gh auth login", safety="This opens GitHub auth only. Do not paste tokens into files."))
    code_cli, _ = run_cmd(["code", "--version"], timeout=8)
    if code_cli != 0:
        issues.append(dict(key="code-cli", status="Manual Only", severity="Medium", problem="VS Code CLI missing", why="Dashboard cannot open repos in VS Code without the code command.", fix="Open VS Code, Command Palette, run Shell Command: Install 'code' command in PATH.", manual="Open VS Code → Command Palette → Shell Command: Install 'code' command in PATH", safety="Manual VS Code configuration only."))
    if not ((run_cmd(["powershell", "-NoProfile", "-Command", "if ((Get-Command aider -ErrorAction SilentlyContinue) -or (Test-Path \"$env:USERPROFILE\\.local\\bin\\aider.exe\")) { exit 0 } else { exit 1 }"], timeout=8)[0]) == 0):
        issues.append(dict(key="aider-missing", status="Fixable", severity="High", problem="Aider missing", why="Worker edits depend on Aider.", fix="Install Aider using aider-install.", manual="python -m pip install aider-install\naider-install", safety="Installs Aider tooling. Does not touch repos.", auto_script=None))
    code_ext, ext_out = ps_inline("code --list-extensions", timeout=12)
    if code_ext != 0 or "saoudrizwan.claude-dev" not in ext_out:
        issues.append(dict(key="cline-missing", status="Fixable", severity="Low", problem="Cline missing", why="Cline gives you a supervised VS Code local assistant.", fix="Install the Cline extension.", manual="code --install-extension saoudrizwan.claude-dev", safety="Installs a VS Code extension only."))
    for repo in read_allowlist():
        info = project_status(repo)
        if not info["exists"]:
            issues.append(dict(key=f"repo-missing-{repo}", status="Needs Review", severity="Medium", problem=f"Repo path missing: {Path(repo).name}", why="An allowlisted path no longer exists.", fix="Fix the path or remove it from the allowlist.", manual="Open Settings → Allowlist Editor", safety="Do not scan the drive. Use explicit paths only."))
            continue
        if info["dirty"] == "Dirty":
            issues.append(dict(key=f"dirty-{repo}", status="Manual Only", severity="High", problem=f"Repo is dirty: {info['name']}", why="AI workers refuse dirty repos to avoid mixing human and AI changes.", fix="Review changes, then commit, stash, or discard manually.", manual="git status\ngit diff\ngit add .\ngit commit -m \"save work before AI run\"\ngit stash push -m \"manual stash before AI run\"", safety="No automatic stash or discard is performed.", repo_path=repo))
        package = Path(repo) / "package.json"
        if package.exists():
            try:
                data = json.loads(package.read_text(encoding="utf-8"))
                engines = data.get("engines", {})
                node_req = engines.get("node")
                if node_req:
                    node_code, node_out = run_cmd(["node", "--version"], timeout=5)
                    if node_code == 0 and "<" in node_req:
                        issues.append(dict(key=f"node-engine-{repo}", status="Manual Only", severity="Medium", problem=f"Node engine constraint in {info['name']}", why=f"package.json engines.node is {node_req}; current Node is {node_out.strip()}.", fix="Use Volta or nvm-windows if validation shows Node mismatch.", manual="volta install node@20\n# or use nvm-windows manually", safety="Do not auto-change global Node."))
            except Exception:
                pass
        if not (Path(repo) / "node_modules").exists() and info["package"]:
            pm = "pnpm" if (Path(repo) / "pnpm-lock.yaml").exists() else "yarn" if (Path(repo) / "yarn.lock").exists() else "npm"
            issues.append(dict(key=f"install-needed-{repo}", status="Needs Review", severity="Medium", problem=f"Dependencies missing: {info['name']}", why="Validation may not run without installed dependencies.", fix=f"Install dependencies with {pm} after confirming this repo is safe.", manual=f"{pm} install", safety="Requires manual confirmation. No package upgrade request is made.", repo_path=repo))
    latest_worker = latest_matching(["web-ai-worker-*.log", "repo-validation-*.log"])
    if latest_worker:
        preview = file_preview(latest_worker, 9000)
        if re.search(r"Exit code.*: [1-9]|ERROR|FAIL|failed", preview, re.I):
            label = "Build Failure" if "build" in preview.lower() else "Validation failed"
            issues.append(dict(key="validation-failed", status="Needs Review", severity="High", problem=label, why="The latest validation log contains a failure.", fix="Open the log, run reviewer, then fix exactly one validation error.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\run-ai-reviewer.ps1 -RepoPath \"C:\\path\\to\\repo\"", safety="Reviewer is read-only. Do not rerun workers until repo is clean.", log_path=latest_worker))
    exists, task_out = scheduled_info()
    if exists and re.search(r"LastTaskResult\s*:\s*(?!0\b)\S+", task_out):
        issues.append(dict(key="scheduled-failed", status="Fixable", severity="High", problem="Scheduled worker failed", why="The Windows scheduled task reports a nonzero last result.", fix="Disable scheduled worker, inspect latest log, then dry-run manually.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\remove-scheduled-web-worker.ps1", safety="Disables only the scheduled task. It does not delete repos or models.", auto_script="remove-scheduled-web-worker.ps1", log_path=latest_matching(["web-ai-worker-*.log"]), emergency=True))
    lock_dir = ROOT / "locks"
    for lock in latest_files(lock_dir, 20, "*.lock"):
        age = datetime.now() - datetime.fromtimestamp(lock.stat().st_mtime)
        if age > timedelta(hours=2):
            issues.append(dict(key=f"stale-lock-{lock.name}", status="Manual Only", severity="Medium", problem="Worker lock exists too long", why="A per-repo lock may be stale if no worker is running.", fix="Verify no worker is running, then remove the stale lock manually.", manual=f"Get-Process | Where-Object {{$_.ProcessName -match 'powershell|pwsh|python'}}\nRemove-Item -LiteralPath \"{lock}\"", safety="Do not delete locks while a worker is running."))
    for name, profile in load_profiles().items():
        if profile.get("paid") and profile.get("apiKeyEnvVar") and not key_present(profile.get("apiKeyEnvVar")):
            issues.append(dict(key=f"key-{profile.get('provider')}", status="Info", severity="Low", problem=f"Provider key missing: {profile.get('provider')}", why="Paid turbo mode is unavailable for this provider.", fix="Set the key only if you want manual paid turbo mode.", manual=f"setx {profile.get('apiKeyEnvVar')} \"YOUR_KEY\"", safety="Never store keys in repos. Scheduled workers remain local-only."))
    if not issues:
        issues.append(dict(key="healthy", status="Info", severity="Low", problem="No major issues detected", why="Core local stack appears healthy.", fix="Continue with dry-run first on any repo.", manual="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\doctor-local-ai.ps1", safety="No automatic changes."))
    return issues


def page_fix_center() -> None:
    section_intro("Fix Center", "See what failed, why it matters, and the safest recovery action.", [("Recovery", "info"), ("No secrets", "ready")])
    issues = collect_issues()
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    issues = sorted(issues, key=lambda i: severity_order.get(i.get("severity", "Low"), 9))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Issues", str(len(issues)), "Detected checks", "info")
    with c2:
        card("High/Critical", str(sum(1 for i in issues if i["severity"] in ("High", "Critical"))), "Act first", "danger" if any(i["severity"] in ("High", "Critical") for i in issues) else "ready")
    with c3:
        card("Fixable", str(sum(1 for i in issues if i["status"] == "Fixable")), "Safe buttons available", "ready")
    with c4:
        card("Manual Only", str(sum(1 for i in issues if i["status"] == "Manual Only")), "Needs your decision", "warn")
    st.markdown("### Recovery Actions")
    for issue in issues:
        with st.container():
            issue_card(**issue)
            st.markdown("---")
    st.subheader("Diagnostic Bundle")
    st.write("Creates a zip with non-secret diagnostics, latest logs/reports, task status, and versions.")
    if st.button("Create Diagnostic Bundle"):
        code, out = run_ps("make-diagnostic-bundle.ps1", timeout=120)
        action_result("Diagnostic bundle", code, out)
    st.subheader("Recovery Guide")
    st.write("Manual fallback guide:")
    st.code("C:\\ai-agent-tools\\configs\\RECOVERY_GUIDE.md")
    if st.button("Open Recovery Guide"):
        os.startfile(str(CONFIGS / "RECOVERY_GUIDE.md"))


def tool_statuses() -> dict:
    code_ext, ext_out = ps_inline("code --list-extensions", timeout=12)
    code_gh, _ = run_cmd(["gh", "auth", "status"], timeout=12)
    code_aider, _ = ps_inline("if ((Get-Command aider -ErrorAction SilentlyContinue) -or (Test-Path \"$env:USERPROFILE\\.local\\bin\\aider.exe\")) { exit 0 } else { exit 1 }", timeout=8)
    _, docker_out = ps_inline("if (Get-Command docker -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }", timeout=8)
    code_pmcp, pmcp_out = run_cmd(["npm", "list", "-g", "@playwright/mcp", "--depth=0"], timeout=20)
    scheduled, _ = scheduled_info()
    return {
        "ollama": test_http("http://127.0.0.1:11434/api/tags"),
        "proxy": test_http("http://127.0.0.1:8082/v1/models", "@{ 'x-api-key'='freecc' }"),
        "cline": code_ext == 0 and "saoudrizwan.claude-dev" in ext_out,
        "aider": code_aider == 0,
        "docker": "yes" in docker_out.lower(),
        "openhands": test_http("http://127.0.0.1:3000"),
        "playwright_mcp": code_pmcp == 0 and "@playwright/mcp" in pmcp_out,
        "github": code_gh == 0,
        "scheduled": scheduled,
    }


def integration_card(title: str, purpose: str, ready: bool, status: str, safety: str, docs: str | None = None, start_script: str | None = None, stop_script: str | None = None, command: str | None = None) -> None:
    st.markdown(f"### {title} {chip(status, 'ready' if ready else 'warn')}", unsafe_allow_html=True)
    st.write(purpose)
    st.caption(f"Safety: {safety}")
    if command:
        st.code(command)
    cols = st.columns(3)
    with cols[0]:
        if start_script and st.button(f"Start/Open", key=f"start-{title}"):
            code, out = run_ps(start_script, timeout=300)
            action_result(title, code, out)
    with cols[1]:
        if stop_script and st.button("Stop", key=f"stop-{title}"):
            code, out = run_ps(stop_script, timeout=120)
            action_result(f"Stop {title}", code, out)
    with cols[2]:
        if docs and st.button("Docs", key=f"docs-{title}"):
            os.startfile(docs)


def page_tools_integrations() -> None:
    section_intro("Tools / Integrations", "Mission Control launches, monitors, gates, and routes existing agent tools instead of rebuilding them.", [("Orchestration", "info"), ("Existing Tools", "ready")])
    statuses = tool_statuses()
    st.info("Recommended flow: Dashboard chooses route -> Cline/Aider/OpenHands does work -> Playwright/GitHub validates -> Dashboard shows report -> you approve.")
    cols = st.columns(2)
    with cols[0]:
        integration_card("Ollama", "Free local model runtime for local coding agents.", statuses["ollama"], "Ready" if statuses["ollama"] else "Offline", "Local-only. No API billing.", start_script="start-local-model-stack.ps1", docs=str(CONFIGS / "LOCAL_MODELS.md"))
        integration_card("Cline", "VS Code interactive coding agent and MCP client.", statuses["cline"], "Installed" if statuses["cline"] else "Missing", "Approve tool calls; avoid broad filesystem access.", start_script="open-ai-tools-vscode.ps1", docs=str(CONFIGS / "CLINE_MCP_TOOLS.md"), command="Provider: Ollama\nBase URL: http://localhost:11434\nModel: qwen2.5-coder:14b")
        integration_card("Aider", "Git-aware focused code editing worker.", statuses["aider"], "Installed" if statuses["aider"] else "Missing", "Use AI branches. No push.", docs=str(CONFIGS / "AIDER_LOCAL_SETUP.md"), command="aider --model ollama/qwen2.5-coder:14b")
        integration_card("Playwright MCP", "Browser automation server for agents to inspect pages and create better tests.", statuses["playwright_mcp"], "Installed" if statuses["playwright_mcp"] else "Optional", "Use local/dev URLs first. Do not enter secrets.", docs=str(CONFIGS / "PLAYWRIGHT_MCP_SETUP.md"), command="npx @playwright/mcp")
        integration_card("GitHub CLI", "Issues, PRs, Actions, and pipeline log inspection.", statuses["github"], "Authenticated" if statuses["github"] else "Not Connected", "Inspect logs. Do not push from dashboard.", command="gh run list --limit 10")
    with cols[1]:
        integration_card("free-claude-code", "Claude Code-compatible local proxy to Ollama.", statuses["proxy"], "Online" if statuses["proxy"] else "Offline", "Session-scoped env vars only.", start_script="start-free-claude-code-proxy.ps1", stop_script="stop-local-model-stack.ps1", docs=str(CONFIGS / "FREE_CLAUDE_CODE_SETUP.md"), command="powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\start-claude-code-local.ps1")
        integration_card("OpenHands", "Optional autonomous dev workspace for agentic repo experiments.", statuses["openhands"], "Running" if statuses["openhands"] else ("Docker Missing" if not statuses["docker"] else "Optional"), "Use disposable repo first; do not mount broad folders.", start_script="start-openhands.ps1", stop_script="stop-openhands.ps1", docs=str(CONFIGS / "OPENHANDS_SETUP.md"), command="Model: openai/qwen2.5-coder:14b\nBase URL: http://host.docker.internal:11434/v1\nAPI key: local-llm")
        st.markdown(f"### Aider Browser UI {chip('Manual', 'warn')}", unsafe_allow_html=True)
        st.write("Optional browser UI for manual Aider sessions on one allowlisted repo.")
        repos = read_allowlist()
        repo = st.selectbox("Repo for Aider Browser", repos, key="tools-aider-browser-repo") if repos else None
        st.caption("Can edit files. Launcher uses --no-auto-commits and does not push.")
        if st.button("Start Aider Browser UI") and repo:
            code, out = run_ps("start-aider-browser.ps1", "-RepoPath", repo, timeout=120)
            action_result("Aider Browser UI", code, out)
        if st.button("Aider Browser Docs"):
            os.startfile(str(CONFIGS / "AIDER_BROWSER_UI.md"))
        integration_card("Scheduled Worker", "Existing safe local-only periodic worker with locks, logs, and reports.", statuses["scheduled"], "Enabled" if statuses["scheduled"] else "Disabled", "Local Ollama only. No commit, no push.", docs=str(CONFIGS / "DASHBOARD_SETUP.md"), command="install-scheduled-web-worker.ps1 -RepoPath <repo> -BaseBranch main -IntervalHours 2")
    with st.expander("Architecture decision"):
        st.code(file_preview(CONFIGS / "TOOL_ORCHESTRATION.md", 12000))


def page_workflow_wizard() -> None:
    section_intro("Workflow Wizard", "Pick the job. Mission Control recommends the right existing tool and the safest first command.", [("Route", "info"), ("Do Not Rebuild", "ready")])
    choice = st.selectbox("What do you want to do?", [
        "Vibe code a small UI change",
        "Fix build/lint/type errors",
        "Investigate a broken page",
        "Explore a repo deeply",
        "Run safe automated maintenance",
        "Check GitHub pipeline failure",
        "Use Claude Code-style local mode",
    ])
    routes = {
        "Vibe code a small UI change": ("Cline or Aider", "Interactive UI work benefits from Cline in VS Code; focused edits can use Aider.", "Open VS Code workspace, dry-run first, make one small AI branch.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\open-ai-tools-vscode.ps1 -OpenDashboard"),
        "Fix build/lint/type errors": ("Aider + validation runner", "Aider is Git-aware and validation output gives concrete failures.", "Run validation, then fix exactly one error.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\repo-validation-runner.ps1 -RepoPath \"C:\\path\\to\\repo\""),
        "Investigate a broken page": ("Cline + Playwright MCP", "Browser inspection should use browser tools instead of guessing.", "Start dev server, use Playwright MCP or repo e2e tests.", "npx @playwright/mcp"),
        "Explore a repo deeply": ("OpenHands or Cline", "Use an existing agent workspace for broad exploration.", "Use disposable repo first for OpenHands; keep approvals on.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\install-openhands-notes.ps1"),
        "Run safe automated maintenance": ("Scheduled local worker", "Your custom worker is built for local-only periodic safe tasks.", "Dry-run and manual pass first; schedule only clean repos.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\install-scheduled-web-worker.ps1 -RepoPath \"C:\\path\\to\\repo\" -BaseBranch main -IntervalHours 2"),
        "Check GitHub pipeline failure": ("GitHub CLI + DevOps AI", "GitHub CLI exposes Actions logs and PR state.", "Run pipeline checker, then use DevOps prompt.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\check-github-pipelines.ps1 -RepoPath \"C:\\path\\to\\repo\""),
        "Use Claude Code-style local mode": ("free-claude-code proxy", "It translates Claude Code-style API calls to local-compatible models.", "Start proxy, then launch Claude Code local script.", "powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\start-claude-code-local.ps1"),
    }
    tool, why, checklist, command = routes[choice]
    c1, c2 = st.columns(2)
    with c1:
        card("Recommended Tool", tool, why, "info")
    with c2:
        card("Safety Checklist", "Manual approval", checklist, "ready")
    st.subheader("Command")
    st.code(command)
    st.markdown("### What this will NOT do")
    st.markdown("- no commit\n- no push\n- no secrets\n- no paid API unless explicitly selected\n- no scheduled mode unless explicitly enabled")
    if st.button("Open Tool Orchestration Docs"):
        os.startfile(str(CONFIGS / "TOOL_ORCHESTRATION.md"))


def page_projects() -> None:
    section_intro("Projects", "Manage explicit repo paths. No drive scanning, no edits unless you press an action button.", [("Multi-project", "info"), ("Safe checks first", "ready")])
    repos = read_allowlist()
    with st.expander("Add Project", expanded=not repos):
        new_path = st.text_input("Repo path", placeholder=r"H:\Github\my-web-app")
        if st.button("Validate and Add Project"):
            ok, msg = validate_project_path(new_path)
            if ok:
                repos.append(str(Path(new_path)))
                write_allowlist(repos)
                st.success(f"Added project: {new_path}")
                st.rerun()
            else:
                st.error(msg)
    if not repos:
        st.info("No projects yet. Add one explicit repo path above.")
        return
    for path in repos:
        info = project_status(path)
        tone = "ready" if info["risk"] == "Low" else "warn" if info["risk"] == "Needs Review" else "danger"
        with st.container():
            st.markdown(f"### {info['name']} {chip(info['risk'], tone)} {chip(info['dirty'], 'ready' if info['dirty']=='Clean' else 'warn')}", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                card("Framework", info["framework"], info["packageManager"], "info")
            with c2:
                card("Branch", info["branch"], "Current branch", "info")
            with c3:
                card("Next Action", info["nextAction"], info["why"], tone)
            with c4:
                card("Scheduled", "Check Scheduler", "One global local task", "muted")
            st.caption(info["path"])
            with st.expander("Actions and details"):
                if info["dirty"] == "Dirty":
                    st.warning("This repo is dirty. Open Fix Center or Morning Review before worker actions.")
                st.write("Package scripts:", ", ".join(info["scripts"]) if info["scripts"] else "none")
                st.write("Latest AI branches:", ", ".join(info["aiBranches"]) if info["aiBranches"] else "none")
                st.write(f"Latest report: `{info['latestReport'] or 'none'}`")
                st.write(f"Latest log: `{info['latestLog'] or 'none'}`")
                render_repo_actions(path, info["branch"] if info["branch"] != "Unknown" else settings["defaultBaseBranch"], "projects")


def page_vibe_code() -> None:
    section_intro("Vibe Code", "Pick a project, choose a small task style, run a dry-run first, then one controlled local AI pass.", [("One task", "ready"), ("AI branch", "info"), ("No push", "ready")])
    repos = read_allowlist()
    if not repos:
        st.info("Add a project first on the Projects page.")
        return
    project = st.selectbox("Project", repos)
    info = project_status(project)
    mode = st.radio("Mode", ["Free Local Safe Mode", "Free Local Worker Pass", "Paid Turbo Manual Mode"], horizontal=True)
    if mode == "Paid Turbo Manual Mode":
        any_key = any(key_present(p.get("apiKeyEnvVar")) for p in load_profiles().values() if p.get("paid"))
        if not any_key:
            st.warning("Paid turbo is disabled because no provider keys are present. Scheduled workers never use paid providers.")
    task_style = st.selectbox("Task style", ["Fix build/type errors", "Polish one UI component", "Improve README/docs", "Add one test", "Improve accessibility", "Analyze GitHub pipeline", "Custom small task"])
    custom = ""
    if task_style == "Custom small task":
        custom = st.text_area("Small task request", placeholder="Keep this tiny. Example: improve empty state text on one component.")
    st.markdown("### Safety Summary")
    st.markdown(
        "- will create an AI branch for a real pass\n- will not commit\n- will not push\n- will not touch secrets or .env\n- one small task only\n- validation and report required"
    )
    if info["dirty"] == "Dirty":
        st.error("Blocked: repo is dirty. Open Fix Center or run Morning Review before worker actions.")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Dry Run First"):
            code, out = run_ps("run-web-ai-worker.ps1", "-RepoPath", project, "-BaseBranch", settings["defaultBaseBranch"], "-DryRun", timeout=240)
            action_result("Dry run", code, out)
    with c2:
        confirm = st.checkbox("I understand this may edit files on an AI branch.")
        if st.button("Run One Local AI Pass") and confirm:
            if info["dirty"] == "Dirty":
                st.error("Refusing: repo is dirty.")
            else:
                code, out = run_ps("run-web-ai-worker.ps1", "-RepoPath", project, "-BaseBranch", settings["defaultBaseBranch"], timeout=1800)
                action_result("Local AI pass", code, out)
    with c3:
        if st.button("Run Reviewer"):
            code, out = run_ps("run-ai-reviewer.ps1", "-RepoPath", project, timeout=300)
            action_result("Reviewer", code, out)
    with st.expander("Plain English explanation"):
        st.write("Vibe Code mode is for small controlled changes. The AI gets one task, validates it, writes a report, and stops.")


def page_runs() -> None:
    section_intro("Runs", "A clean timeline of AI activity. Raw logs stay hidden until you open them.", [("Timeline", "info")])
    items = run_list()
    if not items:
        st.info("No logs or reports yet.")
        return
    scope = st.radio("Time range", ["Today", "Week", "All"], horizontal=True)
    now = datetime.now()
    if scope == "Today":
        items = [i for i in items if i["time"].date() == now.date()]
    elif scope == "Week":
        items = [i for i in items if i["time"] >= now - timedelta(days=7)]
    status_filter = st.selectbox("Status", ["All", "Info", "Needs Review"])
    if status_filter != "All":
        items = [i for i in items if i["status"] == status_filter]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Runs", str(len(items)), scope, "info")
    with c2:
        card("Needs Review", str(sum(1 for i in items if i["status"] == "Needs Review")), "Manual decision", "warn")
    with c3:
        card("Failed", str(sum(1 for i in items if "fail" in file_preview(Path(i["file"]), 1500).lower())), "Log scan", "danger")
    with c4:
        card("Free vs Paid", "Local default", "Paid logs only when manual", "ready")
    for item in items[:60]:
        with st.expander(f"{item['time'].strftime('%Y-%m-%d %H:%M')} · {item['action']} · {item['name']}"):
            st.write(f"Status: `{item['status']}`")
            st.write(f"File: `{item['file']}`")
            st.code(file_preview(Path(item["file"]), 5000))


def page_morning_review() -> None:
    section_intro("Morning Review", "Understand overnight or AI branch work. This page never commits, discards, or pushes.", [("No edits", "ready"), ("Review only", "info")])
    repos = read_allowlist()
    if st.button("Review All AI Work"):
        for path in repos:
            st.markdown(f"#### {Path(path).name}")
            code, out = run_ps("morning-review.ps1", "-RepoPath", path, timeout=120)
            action_result(f"Morning review {Path(path).name}", code, out)
    for path in repos:
        info = project_status(path)
        with st.expander(f"{info['name']} · {info['dirty']} · {info['branch']}"):
            st.write(f"Changed state: `{info['dirty']}`")
            st.write("AI branches:", ", ".join(info["aiBranches"]) if info["aiBranches"] else "none")
            st.write(f"Recommended action: **{info['nextAction']}**")
            st.write(info["why"])


def page_scheduler() -> None:
    section_intro("Scheduler", "Controlled local-only scheduling. Paid models are never scheduled here.", [("Local only", "ready"), ("Manual enable", "warn")])
    exists, out = scheduled_info()
    c1, c2 = st.columns(2)
    with c1:
        card("Scheduled Task", "Enabled/Installed" if exists else "Disabled", "Local Web AI Worker", "warn" if exists else "muted")
    with c2:
        lock_files = latest_files(ROOT / "locks", 20, "*.lock")
        card("Repo Locks", str(len(lock_files)), "Active worker locks", "info" if lock_files else "ready")
    with st.expander("Task details", expanded=exists):
        st.code(out or "Scheduled task is not installed.")
    if exists and "LastTaskResult" in out and "LastTaskResult : 0" not in out:
        st.warning("Scheduled task may need attention. Open Fix Center for recovery actions.")
    repos = read_allowlist()
    if repos:
        selected = st.selectbox("Repo for scheduling", repos)
        interval = st.selectbox("Interval", [1, 2, 4, 8], index=1)
        st.markdown("- local Ollama only\n- creates AI branches\n- no commit\n- no push\n- refuses dirty repos")
        confirm = st.checkbox(f"I understand this will run local AI every {interval} hour(s) on an AI branch.")
        if st.button("Enable Scheduled Worker") and confirm:
            code, out = run_ps("install-scheduled-web-worker.ps1", "-RepoPath", selected, "-BaseBranch", settings["defaultBaseBranch"], "-IntervalHours", str(interval), timeout=120)
            action_result("Enable scheduler", code, out)
    st.error("Emergency stop removes the scheduled worker task. It does not delete repos or models.")
    confirm_stop = st.checkbox("I want to disable the scheduled worker.")
    if st.button("Emergency Stop Scheduled Worker") and confirm_stop:
        code, out = run_ps("remove-scheduled-web-worker.ps1", timeout=120)
        action_result("Emergency stop", code, out)


def page_models() -> None:
    section_intro("Models", "Local models are free. They use your GPU and do not bill API tokens.", [("Free Local", "ready"), ("GPU if available", "info")])
    c1, c2, c3 = st.columns(3)
    code, models = run_cmd(["ollama", "list"], timeout=10)
    code_ps, ps = run_cmd(["ollama", "ps"], timeout=10)
    with c1:
        card("Ollama", "Online" if test_http("http://127.0.0.1:11434/api/tags") else "Offline", "Local model server", "ready" if code == 0 else "danger")
    with c2:
        card("Default Model", "Available" if "qwen2.5-coder:14b" in models else "Missing", "qwen2.5-coder:14b", "ready" if "qwen2.5-coder:14b" in models else "danger")
    with c3:
        card("GPU Hint", "Active" if "GPU" in ps else "Unknown", "From ollama ps", "ready" if "GPU" in ps else "warn")
    st.write("Installed models")
    st.code(models or "No model list available.")
    st.write("Running models")
    st.code(ps or "No running models.")
    cols = st.columns(5)
    buttons = [
        ("Start Local Stack", "start-local-model-stack.ps1"),
        ("Health Check", "health-local-ai-stack.ps1"),
        ("Test Local Model", "test-local-model.ps1"),
        ("Start Proxy", "start-free-claude-code-proxy.ps1"),
        ("Test Proxy", "test-free-claude-code-proxy.ps1"),
    ]
    for idx, (label, script) in enumerate(buttons):
        with cols[idx]:
            if st.button(label):
                code, out = run_ps(script, timeout=300)
                action_result(label, code, out)
    st.info("Best for small scoped edits, validation fixes, docs, tests, and UI polish. Use stronger paid/Claude/Codex for deep architecture.")


def page_providers() -> None:
    section_intro("Providers", "Paid providers are manual turbo mode. They are not used by scheduled workers.", [("Paid Optional", "warn"), ("Manual Only", "info")])
    profiles = {k: v for k, v in load_profiles().items() if v.get("paid")}
    if st.button("Manage Provider Secrets"):
        code, out = run_ps("manage-provider-secrets.ps1", "-Action", "List", timeout=60)
        action_result("Secrets status", code, out)
    if st.button("Compare Models Local Only"):
        code, out = run_ps("compare-models.ps1", timeout=240)
        action_result("Compare models", code, out)
    st.warning("Do not run paid providers 24/7 unless you add budget controls.")
    cols = st.columns(3)
    for idx, (name, p) in enumerate(profiles.items()):
        with cols[idx % 3]:
            present = key_present(p.get("apiKeyEnvVar"))
            st.markdown(f"### {p.get('provider','provider').title()} {chip('Paid Optional','warn')}", unsafe_allow_html=True)
            st.write(p.get("role", ""))
            st.write(f"Key present: `{'yes' if present else 'no'}`")
            st.write(f"Base URL: `{p.get('baseUrl')}`")
            st.write(f"Model: `{p.get('model')}`")
            last = latest_files(LOGS, 1, f"provider-test-{p.get('provider')}*.log")
            st.caption(f"Last result: {last[0].name if last else 'none'}")
            if st.button(f"Test {p.get('provider')}", key=f"provider-test-{name}"):
                if not present:
                    st.error(f"Missing {p.get('apiKeyEnvVar')}. Use the secrets helper first.")
                else:
                    code, out = run_ps("test-provider-model.ps1", "-ProviderName", p.get("provider"), "-BaseUrl", p.get("baseUrl"), "-Model", p.get("model"), "-ApiKeyEnvVar", p.get("apiKeyEnvVar"), timeout=180)
                    action_result(f"Test {p.get('provider')}", code, out)
    with st.expander("Provider profile JSON"):
        st.code(file_preview(PROFILES, 12000))


def page_logs() -> None:
    section_intro("Logs & Reports", "Find recent activity without dumping huge logs by default.", [("Searchable", "info"), ("Sanitized", "ready")])
    all_files = latest_files(LOGS, 200) + latest_files(REPORTS, 200) + latest_files(TEAM_REPORTS, 100)
    query = st.text_input("Search file name or preview")
    file_type = st.selectbox("Type", ["All", "worker", "review", "provider", "dashboard", "doctor"])
    filtered = []
    for path in all_files:
        hay = path.name.lower()
        if file_type != "All" and file_type not in hay.lower():
            continue
        if query and query.lower() not in hay and query.lower() not in file_preview(path, 1000).lower():
            continue
        filtered.append(path)
    st.write(f"{len(filtered)} files")
    for path in filtered[:50]:
        with st.expander(f"{path.name} · {datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"Path: `{path}`")
            st.code(file_preview(path, 8000))


def page_vscode() -> None:
    section_intro("VS Code", "Open the workspace, run AI tasks, and use Cline with Ollama.", [("Workspace", "info")])
    workspace = ROOT / "Local AI Control Center.code-workspace"
    st.write(f"Workspace: `{workspace}`")
    st.markdown("Recommended flow: open project, run dry-run, run one worker pass, review diff, commit manually.")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Open Workspace"):
            code, out = run_ps("open-ai-tools-vscode.ps1", timeout=60)
            action_result("Open workspace", code, out)
    with c2:
        if st.button("Open Workspace + Dashboard"):
            code, out = run_ps("open-ai-tools-vscode.ps1", "-OpenDashboard", timeout=90)
            action_result("Open workspace + dashboard", code, out)
    with c3:
        if st.button("Doctor Check"):
            code, out = run_ps("doctor-local-ai.ps1", timeout=180)
            action_result("Doctor", code, out)
    code_ext, ext_out = ps_inline("code --list-extensions", timeout=12)
    st.write("Status")
    st.code(ext_out if code_ext == 0 else "VS Code CLI not available.")
    st.write("Available AI tasks")
    st.code("AI: Open Dashboard\nAI: Health Check\nAI: Stack Monitor\nAI: Provider Health\nAI: Manage Provider Secrets\nAI: Test Proxy\nAI: Compare Models Local Only")


def page_settings() -> None:
    section_intro("Settings", "Control defaults and allowlisted repos. Secrets are not stored here.", [("Safety Mode", "ready" if settings.get("safetyMode") else "warn")])
    new_settings = settings.copy()
    new_settings["defaultModel"] = st.text_input("Default model", value=settings["defaultModel"])
    new_settings["defaultBaseBranch"] = st.text_input("Default base branch", value=settings["defaultBaseBranch"])
    new_settings["defaultIntervalHours"] = st.selectbox("Default interval", [1, 2, 4, 8], index=[1, 2, 4, 8].index(settings.get("defaultIntervalHours", 2)))
    new_settings["safetyMode"] = st.toggle("Safety mode", value=bool(settings.get("safetyMode", True)))
    new_settings["advancedMode"] = st.toggle("Advanced mode", value=bool(settings.get("advancedMode", False)))
    if st.button("Save Settings"):
        save_settings(new_settings)
        st.success("Settings saved.")
        st.rerun()
    st.subheader("Allowlist Editor")
    current = "\n".join(read_allowlist())
    edited = st.text_area("One explicit repo path per line", value=current, height=160)
    if st.button("Save Allowlist"):
        write_allowlist([line.strip() for line in edited.splitlines() if line.strip()])
        st.success("Allowlist saved.")
    st.warning("Do not save secrets here. Use Manage Provider Secrets.")


def page_help() -> None:
    section_intro("Help", "Plain-English guide to local multi-project vibe coding.", [("Beginner friendly", "info")])
    st.markdown(
        """
### What this app does
It coordinates local AI coding tools for your repos: scans, dry-runs, one-pass workers, reviews, logs, and optional scheduling.

### Free Local Mode
Local Ollama models run on your machine. They do not bill API tokens.

### AI Branch
The worker creates a branch named `ai/...`, makes one small change, validates it, writes a report, and stops.

### Add a Project
Go to Projects, paste one repo path, validate it, and add it. The app never scans your whole disk.

### Dry-run
Dry-run checks repo safety and validation commands. It does not create a branch or edit files.

### One AI Pass
One controlled worker run. It does not commit or push. You review the diff manually.

### Morning Review
Read-only review of AI branches, diffs, reports, and recommended next action.

### Schedule
Local-only. Enable only after clean manual runs. Emergency stop removes the scheduled task.

### What not to automate
Auth, payments, secrets, deployment config, database migrations, dependency upgrades, and major redesigns.

### Emergency stop
```powershell
powershell -ExecutionPolicy Bypass -File C:\\ai-agent-tools\\scripts\\remove-scheduled-web-worker.ps1
```

### Paid providers
Paid providers are manual turbo mode only. Scheduled workers do not use them.
"""
    )


PAGES = {
    "Home": page_home,
    "Fix Center": page_fix_center,
    "Tools / Integrations": page_tools_integrations,
    "Workflow Wizard": page_workflow_wizard,
    "Projects": page_projects,
    "Vibe Code": page_vibe_code,
    "Runs": page_runs,
    "Morning Review": page_morning_review,
    "Scheduler": page_scheduler,
    "Models": page_models,
    "Providers": page_providers,
    "Logs & Reports": page_logs,
    "VS Code": page_vscode,
    "Settings": page_settings,
    "Help": page_help,
}

try:
    PAGES[page]()
except Exception as exc:
    st.error("This panel hit a recoverable error. The dashboard stayed alive.")
    st.code(sanitize(str(exc)))
