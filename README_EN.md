# 🌉 CodeBridge Gateway

> **Local gateway connecting Codex to NVIDIA NIM.**

[![License MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Bilingual Docs](https://img.shields.io/badge/Docs-English%20%7C%20Español-orange.svg)](#documentation)

**[ English ] | [ Spanish Version (README.md) ](README.md)**

```text
Codex → OpenAI Responses API → CodeBridge → NVIDIA NIM
```

## What It Does

CodeBridge is a lightweight local gateway that lets you use NVIDIA NIM models
with Codex as an alternative backend — routing everyday coding tasks to NVIDIA
and reserving your premium OpenAI credits for work that truly needs them.

## Why It Exists

Codex uses the OpenAI Responses API. NVIDIA NIM is OpenAI-compatible, but only
reliably at the Chat Completions level on their hosted service. CodeBridge:

1. Accepts Responses API requests from Codex
2. Translates to NVIDIA's supported `/v1/chat/completions` endpoint
3. Returns Responses API format back to Codex

Completely transparent to Codex.

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  Codex                                                    │
│  (sends Responses API requests)                           │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /v1/responses
                       ▼
┌──────────────────────────────────────────────────────────┐
│  CodeBridge Gateway  (http://127.0.0.1:8787)             │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Authentication     Telemetry    Model Router   │     │
│  │  (local token)      (local only) (deterministic)│     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────┐     │
│  │  Protocol Adapter                               │     │
│  │  Responses API ↔ Chat Completions               │     │
│  └──────────────────────┬──────────────────────────┘     │
└─────────────────────────┼────────────────────────────────┘
                          │ POST /v1/chat/completions
                          ▼
┌──────────────────────────────────────────────────────────┐
│  NVIDIA NIM  (integrate.api.nvidia.com)                  │
└──────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- NVIDIA API key ([get one here](https://build.nvidia.com))
- Codex CLI / OpenAI compatible client

## Quick Start

```bash
# 1. Clone
git clone https://github.com/juanjo101/codebridge.git
cd codebridge

# 2. Setup (Linux/macOS)
bash scripts/setup.sh

# 3. Configure .env with your NVIDIA API key
echo "NVIDIA_API_KEY=nvapi-YOUR_KEY" > .env

# 4. Start CodeBridge
./scripts/cb

# 5. Connect Codex (Transparent for All Projects)
uv run python scripts/configure_codex.py
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

> 💡 **Total Transparency:** Once connected, your global `~/.codex/config.toml` is updated. **Codex will transparently route requests through CodeBridge in all your local projects** without requiring any extra commands.

## AI Agent Deployment Prompt

If you are using an AI agent (Codex, Antigravity, Cursor, etc.), pass this prompt to set up CodeBridge automatically:

```text
Please set up and configure CodeBridge in this environment:
1. Run `bash scripts/setup.sh` (or `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1` on Windows).
2. Ask me for my NVIDIA API Key or set `NVIDIA_API_KEY=your_key` in `.env`.
3. Launch CodeBridge background server using `./scripts/cb mcp` or `uv run codebridge serve`.
4. Run `python scripts/test_nvidia.py` to verify the connection.
5. Run `uv run python scripts/configure_codex.py` to connect Codex to CodeBridge globally.
6. Apply the global skill to your context and make sure to keep the server up.
```

## CLI Reference

```text
./scripts/cb mcp          Quick launcher for CodeBridge MCP
uv run codebridge serve   Start the gateway
uv run codebridge health  Check gateway health
uv run codebridge models  List NVIDIA models
uv run codebridge test    Run NVIDIA connectivity test
```

## 🛡️ Integrated Cybersecurity and Quality Assurance (QA)

CodeBridge now acts as a true **QA Engineer** and **Application Security Engineer**, capable of performing the following operations automatically:

### Security Capabilities (Skill: `codebridge-security` / `codebridge-security-scan`)
- **Vulnerability Detection:** OWASP Top 10, CWE, injections, XSS, broken authentication, etc.
- **Automated Scanning:** Seamless integration with local tools (Semgrep, Bandit, pip-audit, npm audit, Gitleaks, ZAP).
- **Security Score & Remediations:** Security grading, detailed finding analysis, and automated fixes (with explicit authorization).

### QA Capabilities (Skill: `codebridge-qa` / `codebridge-test-generator`)
- **Test Generation:** Unit Tests, Integration, E2E (pytest, unittest, Jest, Vitest, Playwright).
- **QA Strategy:** Code analysis, edge case identification, input validation, and regression testing.
- **Integrated Workflow:** Detect findings → Explain → Auto-fix → Regenerate tests → Security re-scan.

### Daily Usage Commands & Prompts
You can easily invoke these skills by telling the agent (Antigravity/Codex):
- `"cbm audit"` - Unified high-level command to perform a combined Security, Dependency, and QA scan.
- `"Check the security of this project"` or `"Find vulnerabilities"`
- `"Test this project"` or `"Generate integration tests"`
- `"Analyze dependencies and look for exposed secrets"`
## 👤 Author & Creator

Created and maintained by **Juan José Díaz Nerio** ([@juanjo101](https://github.com/juanjo101)).

---

## License

MIT — see [LICENSE](LICENSE)
