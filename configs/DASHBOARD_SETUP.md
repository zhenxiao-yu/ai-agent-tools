# Dashboard Setup

The local dashboard is a Streamlit app that runs on localhost only.

It is now organized as **LOCAL AI MISSION CONTROL**, a dark hacker-themed control center for free local multi-project vibe coding.

Start it:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-dashboard.ps1
```

Open it, starting only if needed:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-dashboard.ps1
```

Open:

```text
http://127.0.0.1:8501
```

## Desktop And Start Menu Shortcuts

Create shortcuts:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\create-dashboard-shortcut.ps1
```

Desktop shortcut:

```text
Local AI Control Center
```

Start Menu shortcut:

```text
Local AI Control Center
```

The shortcut target is `powershell.exe` and it runs:

```powershell
-ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-dashboard.ps1
```

If the dashboard is already running, the shortcut opens the browser. If not, it starts Streamlit first.

## Add Repos

The dashboard reads:

```text
C:\ai-agent-tools\configs\repo-allowlist.txt
```

Add one exact repo path at a time. The dashboard does not scan your whole disk or GitHub folder.

## Repo Actions

From the dashboard, select an allowed repo and run:

- Audit repo
- Dry run
- Repo health scan
- Validation runner
- Reviewer
- Morning review
- GitHub pipelines

The real worker pass is behind an explicit checkbox because it can edit files on an AI branch. It still does not commit or push.

## Logs And Reports

The dashboard shows recent files from:

- `C:\ai-agent-tools\logs`
- `C:\ai-agent-tools\reports`
- `C:\ai-agent-tools\team\reports`

## Scheduled Mode

Scheduled repo worker mode is not enabled by the dashboard.

Use the existing scripts only after several successful manual runs:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\install-scheduled-web-worker.ps1 -RepoPath "C:\path\to\repo" -BaseBranch "main" -IntervalHours 2
```

Disable:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1
```

## Local Model Controls

The dashboard can run:

- health check
- start local model stack
- start free-claude-code proxy
- test proxy

It does not enable proxy auto-start. Enable that separately only after manual approval.

## Pages

- Home: readiness, local/free status, next step.
- Fix Center: issue cards, safe recovery buttons, manual commands, diagnostic bundle.
- Tools / Integrations: launcher cards for Ollama, Cline, Aider, OpenHands, Playwright MCP, free-claude-code, GitHub CLI, and scheduler.
- Workflow Wizard: recommends which existing tool to use for a task.
- Projects: allowlisted repo cards and safe no-edit actions.
- Vibe Code: guided dry-run, one local AI pass, reviewer.
- Runs: timeline of logs and reports.
- Morning Review: read-only overnight/AI-branch review.
- Scheduler: local-only scheduled worker controls and emergency stop.
- Models: Ollama, GPU hint, proxy, model tests.
- Providers: paid optional providers, key-present checks, manual tests.
- Logs & Reports: filtered log/report viewer.
- VS Code: workspace and task shortcuts.
- Settings: allowlist and safe defaults.
- Help: plain-English guide.

## Safety Defaults

- Free local mode is default.
- Paid providers are manual only.
- Scheduled workers are local-only.
- No commit or push buttons exist.
- Risky actions require confirmation.
- Raw logs are hidden behind expandable sections.
- API keys are never displayed.

## Fix Center

Fix Center answers:

- what failed
- why it matters
- how serious it is
- the safest fix
- manual command fallback
- related logs/reports when available

Safe automatic fixes include starting the local model stack, starting the local proxy, disabling the scheduled worker, and creating a diagnostic bundle. Risky repo actions stay manual.

Diagnostic bundle:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\make-diagnostic-bundle.ps1
```

Recovery guide:

```text
C:\ai-agent-tools\configs\RECOVERY_GUIDE.md
```

## Tool Orchestration

The dashboard should route to existing tools instead of rebuilding them.

Main docs:

```text
C:\ai-agent-tools\configs\TOOL_ORCHESTRATION.md
C:\ai-agent-tools\configs\WHAT_NOT_TO_REBUILD.md
C:\ai-agent-tools\configs\OPENHANDS_SETUP.md
C:\ai-agent-tools\configs\AIDER_BROWSER_UI.md
C:\ai-agent-tools\configs\PLAYWRIGHT_MCP_SETUP.md
C:\ai-agent-tools\configs\CLINE_MCP_TOOLS.md
```

## Troubleshooting

- If the shortcut does nothing, run `open-dashboard.ps1` from PowerShell and read the error.
- Startup logs are written to `C:\ai-agent-tools\logs\dashboard-start.log`.
- The dashboard uses a local venv under `C:\ai-agent-tools\dashboard\.venv`.
- If Python packages are broken, delete only that `.venv` folder and rerun `start-dashboard.ps1`.
- If port `8501` is busy, run `start-dashboard.ps1 -Port 8502`.
- For VS Code, open `C:\ai-agent-tools\Local AI Control Center.code-workspace` or run `open-ai-tools-vscode.ps1`.
- In VS Code, run `Tasks: Run Task` and pick an `AI:` task.

## Paid Turbo Providers

The dashboard shows provider health from:

```text
C:\ai-agent-tools\configs\model-profiles.json
```

It never prints API keys. Paid provider tests are manual button clicks only.

Set keys with `setx`, then open a new terminal:

```powershell
setx DEEPSEEK_API_KEY "YOUR_KEY"
setx QWEN_API_KEY "YOUR_KEY"
setx KIMI_API_KEY "YOUR_KEY"
setx SILICONFLOW_API_KEY "YOUR_KEY"
setx OPENROUTER_API_KEY "YOUR_KEY"
setx ZAI_API_KEY "YOUR_KEY"
```

Use local Ollama for scheduled work unless you have explicit paid budget controls.
