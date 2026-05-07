<h1 align="center">🤖 AI Agent Tools</h1>

<p align="center">
  <strong>Local-First AI Coding Workflow for Windows</strong><br>
  Conservative, traceable, and cost-effective AI-assisted development
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#architecture">Architecture</a>
</p>

---

## 🎯 Overview

AI Agent Tools 是一个为 Windows 设计的保守型本地 AI 编码工作流。它让你在付费 API（Codex/Claude）额度用完后，依然能使用本地模型（Ollama）继续高效开发。

**核心理念：小步快跑，人工审核，安全第一**

```
检查 → 选择小任务 → 创建分支 → 编辑 → 验证 → 报告 → 审核 → 停止
```

## ✨ Features

| 功能 | 描述 |
|------|------|
| 🔧 **本地模型支持** | Ollama + qwen2.5-coder:14b，零 API 费用 |
| 🎨 **Web 仪表板** | Streamlit 驱动的可视化控制中心 |
| 📝 **多 Agent 工作流** | PM、Tech Lead、Developer、QA、Reviewer、DevOps |
| ⏰ **定时任务** | Windows 计划任务集成，24/7 自动化 |
| 🔒 **安全优先** | 分支隔离、人工审核、禁止自动推送到主分支 |
| 🌐 **混合模式** | 付费模型做架构，本地模型做实现 |

## 🚀 Quick Start

### 1. 克隆仓库

```powershell
git clone https://github.com/zhenxiao-yu/ai-agent-tools.git
cd ai-agent-tools
```

### 2. 启动本地模型栈

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-model-stack.ps1
```

### 3. 启动仪表板

```powershell
powershell -ExecutionPolicy Bypass -File scripts/open-dashboard.ps1
```

访问 http://127.0.0.1:8501

### 4. 运行健康检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/doctor-local-ai.ps1
```

## 📚 Documentation

### 核心工作流

- **[AGENTS.md](configs/AGENTS.web.template.md)** - Agent 角色定义模板
- **[TOOL_ORCHESTRATION.md](configs/TOOL_ORCHESTRATION.md)** - 工具协调指南
- **[VSCODE_WORKFLOW.md](configs/VSCODE_WORKFLOW.md)** - VS Code 集成工作流
- **[FIRST_REAL_REPO_CHECKLIST.md](configs/FIRST_REAL_REPO_CHECKLIST.md)** - 首次使用清单

### 配置指南

| 文档 | 用途 |
|------|------|
| [CLINE_LOCAL_SETUP.md](configs/CLINE_LOCAL_SETUP.md) | Cline 本地模式配置 |
| [AIDER_LOCAL_SETUP.md](configs/AIDER_LOCAL_SETUP.md) | Aider 本地模式配置 |
| [DASHBOARD_SETUP.md](configs/DASHBOARD_SETUP.md) | 仪表板设置 |
| [PROVIDER_KEYS_SETUP.md](configs/PROVIDER_KEYS_SETUP.md) | 付费 Provider 配置 |
| [RECOVERY_GUIDE.md](configs/RECOVERY_GUIDE.md) | 故障恢复指南 |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VS Code + Cline                       │
│              (交互式 Agent 开发环境)                      │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│              AI Agent Tools Dashboard                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
│  │ Fix     │ │ Projects│ │ Models  │ │ Scheduler   │   │
│  │ Center  │ │         │ │         │ │             │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Ollama     │   │   Aider      │   │  OpenHands   │
│ (本地模型)    │   │ (Git 感知编辑)│   │(自主实验)    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
              ┌─────────────────────┐
              │   GitHub CLI        │
              │   GitHub Actions    │
              │   Playwright        │
              └─────────────────────┘
```

## 🛡️ Safety Rules

- ✅ 禁止直接推送到 main/master
- ✅ 禁止 force push
- ✅ 禁止自动提交（默认）
- ✅ 禁止在 dirty repo 上运行
- ✅ 禁止修改 secrets、.env、密钥、生产配置

## 🧰 Tools & Integrations

| 工具 | 用途 |
|------|------|
| **Ollama** | 本地 LLM 推理 |
| **Cline** | VS Code Agent 扩展 |
| **Aider** | Git 感知的终端编辑 |
| **GitHub CLI** | Issues/PRs/Actions 检查 |
| **Playwright** | 浏览器自动化测试 |
| **Streamlit** | 仪表板 UI |

## 📊 Project Stats

- **Scripts**: 50+ PowerShell 自动化脚本
- **Configs**: 15+ 配置文档
- **Dashboard Pages**: 15+ 功能页面
- **Provider Support**: DeepSeek、Kimi、OpenRouter、Qwen、SiliconFlow 等

## 🤝 Contributing

这个项目采用保守的 AI 辅助开发模式。如果你想贡献：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 使用本地模型进行开发
4. 提交更改 (`git commit -m 'Add amazing feature'`)
5. 推送到分支 (`git push origin feature/amazing-feature`)
6. 创建 Pull Request

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) - 本地模型运行
- [Cline](https://github.com/cline/cline) - VS Code Agent 扩展
- [Aider](https://github.com/paul-gauthier/aider) - Git 感知编辑
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) - 自主开发实验

---

<p align="center">
  Made with ❤️ for cost-effective AI coding
</p>