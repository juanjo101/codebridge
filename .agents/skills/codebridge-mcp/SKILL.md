---
name: codebridge-mcp
description: Invokes CodeBridge Gateway (NVIDIA NIM) via MCP SSE endpoint for code generation, refactoring, and debugging without external API credits. Trigger with codebridge-mcp or cbm.
---

# CodeBridge MCP Skill

Use this skill to route coding tasks, refactoring, and completions through CodeBridge Gateway (NVIDIA NIM).

## ⚡ Lanzador Ultra Corto (Skill: `cbm` / CLI: `cb mcp`)
- **Nombre de Skill corto:** `cbm`
- **Comando CLI:** `./scripts/cb mcp` o `cb mcp`

## Endpoint & Auth
- **MCP SSE URL:** `http://127.0.0.1:8787/mcp/sse`
- **POST Messages URL:** `http://127.0.0.1:8787/mcp/messages`
- **Auth Token:** `FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM`
