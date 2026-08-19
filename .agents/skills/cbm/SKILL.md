---
name: cbm
description: MANDATORY Execution via CodeBridge Gateway (NVIDIA NIM). When triggered, the AI agent MUST execute the user request through CodeBridge by calling python3 scripts/query_cbm.py or sending POST to http://127.0.0.1:8787/v1/responses.
---

# Skill Corto: cbm (CodeBridge MCP / Gateway Execution)

CRÍTICO: Al activar esta habilidad (`cbm`), el agente de IA **DEBE procesar la solicitud del usuario directamente a través de CodeBridge Gateway y NVIDIA NIM** en lugar de generarla localmente sin consultar el servidor.

## ⚡ Instrucción de Ejecución Obligatoria para el Agente

Cuando el usuario incluya `cbm` en su mensaje:
1. El agente local (Antigravity/Gemini) **DEBE recopilar el contexto necesario** antes de llamar a NVIDIA. Esto significa leer el archivo activo, detectar los errores en la terminal o analizar los archivos mencionados por el usuario.
2. El agente **DEBE** empaquetar el prompt del usuario junto con el código/contexto recopilado en un gran string.
3. El agente **DEBE** ejecutar la tarea llamando al Gateway de CodeBridge pasando todo el paquete de información:
   ```bash
   python3 scripts/query_cbm.py "El usuario solicita: <instrucción_del_usuario>. Contexto relevante: <código_y_archivos_activos>"
   ```
4. Presentar la respuesta generada directamente por el modelo de NVIDIA NIM a través de CodeBridge.

## 📡 Endpoints del Gateway
- **Gateway Responses API:** `http://127.0.0.1:8787/v1/responses`
- **MCP SSE URL:** `http://127.0.0.1:8787/mcp/sse`
- **Auth Token:** `FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM`
