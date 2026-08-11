---
name: cbm
description: Short trigger for CodeBridge MCP (NVIDIA NIM Gateway). Use when the user asks for cbm, cb-mcp, or codebridge to generate code, refactor, or debug via NVIDIA NIM.
---

# Skill Corto: cbm (CodeBridge MCP)

Usa esta habilidad para enrutar tareas de programación, refactorización y depuración a través del Gateway local de **CodeBridge (NVIDIA NIM)**.

## ⚡ Lanzamiento Rápido
- **Comando corto:** `./scripts/cb mcp` o `cb mcp`
- **MCP SSE URL:** `http://127.0.0.1:8787/mcp/sse`
- **POST Messages URL:** `http://127.0.0.1:8787/mcp/messages`
- **Auth Token:** `FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM`

## 🎯 Instrucciones de Uso
Al invocar esta habilidad (`cbm`), realiza la generación o refactorización del código enviando las peticiones a CodeBridge en `http://127.0.0.1:8787/v1/responses` o mediante el servidor MCP SSE en `http://127.0.0.1:8787/mcp/sse`.
