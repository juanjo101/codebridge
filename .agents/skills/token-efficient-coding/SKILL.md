---
name: token-efficient-coding
description: >
  Strategy for using NVIDIA via CodeBridge for everyday coding tasks, reserving
  premium OpenAI models for complex work. Use when helping the user decide
  which model to route tasks to, or when advising on the Economy vs Premium split.
---

# Token-Efficient Coding with CodeBridge

## The Core Idea

CodeBridge enables two modes:

**Economy Mode (NVIDIA via CodeBridge)**
- Route to NVIDIA for high-volume, routine tasks
- NVIDIA availability and costs depend on your account/plan

**Premium Mode (OpenAI direct)**
- Route to your premium OpenAI model (e.g., gpt-5.6-sol)
- Higher capability for complex tasks

## When to Use Economy Mode (NVIDIA)

These tasks are typically well-handled by strong NVIDIA models:

- **Everyday coding** — adding functions, fixing bugs, implementing features
- **CRUD operations** — database access, REST APIs, forms
- **Frontend work** — React/Vue/HTML/CSS components, styling
- **SQL queries** — writing, optimizing, explaining queries
- **Tests** — unit tests, mocks, fixtures, test utilities
- **Documentation** — docstrings, READMEs, API documentation
- **Refactoring** — renaming, extracting functions, reorganizing
- **Normal debugging** — stack traces, obvious logic errors
- **Code explanation** — understanding existing code
- **Configuration** — yaml, toml, json, env files
- **Scripts** — bash, python, powershell automation

## When to Use Premium Mode (OpenAI)

These tasks often benefit from the most capable models:

- **Architecture design** — system design, major structural decisions
- **Complex debugging** — multi-system interactions, race conditions, hard bugs
- **Security review** — vulnerability analysis, threat modeling
- **Algorithm design** — novel algorithms, performance-critical code
- **Ambiguous requirements** — when you need the model to figure out what you mean
- **Multi-file refactoring** — large, complex codebase transformations
- **Critical production code** — when correctness is essential

## How to Switch Modes

**Switch to Economy Mode:**
Edit `~/.codex/config.toml`:
```toml
model_provider = "codebridge"
model = "nvidia/your-configured-model"
```

**Switch to Premium Mode:**
```toml
model_provider = "openai"
model = "gpt-5.6-sol"
```

Then restart Codex.

## Important Caveats

- NVIDIA model capabilities vary. Test your chosen model before relying on it.
- NVIDIA API availability, rate limits, and pricing depend on your account.
- Not all NVIDIA models support tool calling — verify with `python scripts/test_nvidia.py`.
- We cannot guarantee specific token savings; this depends on your actual usage.
- Quality may differ between models; validate output for critical tasks.

## Monitoring Usage

```bash
# See how many requests have gone through NVIDIA
curl http://127.0.0.1:8787/usage

# Or via CLI
uv run codebridge usage
```

## Recommended Workflow

1. Start a session → set Economy Mode (NVIDIA)
2. Do routine coding tasks via CodeBridge → NVIDIA
3. When you hit a complex problem → switch to Premium Mode manually
4. After solving the hard problem → switch back to Economy Mode
5. Monitor `/usage` to see NVIDIA workload distribution
