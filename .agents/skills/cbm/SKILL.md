---
name: cbm
description: MANDATORY Execution via CodeBridge Gateway (NVIDIA NIM). When triggered, the AI agent MUST execute the user request through CodeBridge by calling python3 scripts/query_cbm.py or sending POST to http://127.0.0.1:8787/v1/responses.
---

# Skill Corto: cbm (CodeBridge MCP / Gateway Execution)

CRÍTICO: Al activar esta habilidad (`cbm`), el agente de IA **DEBE procesar la solicitud del usuario directamente a través de CodeBridge Gateway y NVIDIA NIM** en lugar de generarla localmente sin consultar el servidor.

## ⚡ Instrucción de Ejecución Obligatoria para el Agente

Cuando el usuario incluya `cbm` en su mensaje:
1. El agente **DEBE** ejecutar la tarea del usuario llamando al Gateway de CodeBridge:
   ```bash
   python3 scripts/query_cbm.py "<instrucción_del_usuario>"
   ```
2. O realizando una petición HTTP `POST http://127.0.0.1:8787/v1/responses` con el token `FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM`.
3. Presentar la respuesta generada directamente por el modelo de NVIDIA NIM a través de CodeBridge.

## 📡 Endpoints del Gateway
- **Gateway Responses API:** `http://127.0.0.1:8787/v1/responses`
- **MCP SSE URL:** `http://127.0.0.1:8787/mcp/sse`
- **Auth Token:** `FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM`
