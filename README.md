# 🌉 CodeBridge Gateway

> **Gateway local ligero que conecta Codex y tus asistentes de IA locales con los modelos de NVIDIA NIM.**

[![Licencia MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Docs Español](https://img.shields.io/badge/Docs-Español-orange.svg)](#-instrucciones-paso-a-paso)

**[ versión en Español ] | [ English Version (README_EN.md) ](README_EN.md)**

```text
Codex / Cliente IDE  ──►  Responses API  ──►  CodeBridge Gateway  ──►  NVIDIA NIM
```

---

## ⚡ ¿Qué es CodeBridge?

**CodeBridge** es un gateway local transparente que te permite conectar **Codex** y tus agentes de IA locales con la infraestructura de **NVIDIA NIM** (Llama 3.3 70B, DeepSeek Coder, Nemotron). 

### 💡 Tu Modo Economía para Programar
Con CodeBridge enrutas el 90% de tus tareas diarias de código (CRUD, refactorización, tests, SQL, documentación) hacia NVIDIA NIM sin consumir tus créditos de APIs de pago, reservando estas últimas solo para tareas de arquitectura de máxima complejidad.

---

## 📐 Arquitectura

```text
┌──────────────────────────────────────────────────────────┐
│  Codex / Asistente de IA                                │
│  (Peticiones en formato OpenAI Responses API)           │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /v1/responses
                       ▼
┌──────────────────────────────────────────────────────────┐
│  CodeBridge Gateway  (http://127.0.0.1:8787)             │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Autenticación     Telemetría    Ruteador       │     │
│  │  (Token local)     (Local)       (Determinist.) │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────┐     │
│  │  Adaptador de Protocolo                         │     │
│  │  Responses API ↔ Chat Completions               │     │
│  └──────────────────────┬──────────────────────────┘     │
└─────────────────────────┼────────────────────────────────┘
                          │ POST /v1/chat/completions
                          ▼
┌──────────────────────────────────────────────────────────┐
│  NVIDIA NIM  (integrate.api.nvidia.com)                  │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Instrucciones Paso a Paso para Hacerlo Funcionar

Sigue estos 5 sencillos pasos para dejar CodeBridge listo en tu entorno de desarrollo en menos de 5 minutos:

### Paso 1: Obtener tu Clave API Gratuita de NVIDIA
1. Entra a [NVIDIA Build Catalog](https://build.nvidia.com).
2. Inicia sesión y genera tu **API Key** en el panel (comienza por `nvapi-...`).

### Paso 2: Descargar e Instalar CodeBridge

#### En Linux / macOS:
```bash
git clone https://github.com/juanjo101/codebridge.git
cd codebridge
bash scripts/setup.sh
```

#### En Windows (PowerShell):
```powershell
git clone https://github.com/juanjo101/codebridge.git
cd codebridge
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

### Paso 3: Configurar tu API Key
Crea el archivo `.env` en la raíz del proyecto y pega tu clave:
```env
NVIDIA_API_KEY=nvapi-tu-clave-aqui
```

### Paso 4: Iniciar CodeBridge y Verificar Conexión
Ejecuta el lanzador ultracorto `cb`:
```bash
./scripts/cb mcp
```

En otra terminal, corre la prueba de conectividad automática con NVIDIA:
```bash
python scripts/test_nvidia.py
```

### Paso 5: Conectar Codex a CodeBridge
Configura Codex automáticamente ejecutando:
```bash
uv run python scripts/configure_codex.py
```
Y exporta tu token de autenticación local en la terminal:
```bash
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

---

## 🤖 Prompt para Despliegue Automático con Agente IA

Si utilizas un asistente o agente de IA en tu IDE (como **Antigravity**, **Codex**, **Cursor** o **Copilot Workspace**), puedes copiar y pegarle este prompt para que instale, configure y despliegue CodeBridge automáticamente por ti:

```text
Por favor despliega y configura CodeBridge en este entorno local ejecutando los siguientes pasos:

1. Revisa los archivos del repositorio y ejecuta el script de instalación automática:
   - En Linux/macOS: `bash scripts/setup.sh`
   - En Windows: `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`
2. Si no existe el archivo `.env`, créalo a partir de `.env.example`. Pídeme mi NVIDIA_API_KEY o configura `NVIDIA_API_KEY=nvapi-KEY` si te la proveo.
3. Inicia el gateway servidor ejecutan en segundo plano: `./scripts/cb mcp`
4. Ejecuta el script de prueba de conectividad `python scripts/test_nvidia.py` para validar la conexión con NVIDIA.
5. Ejecuta `uv run python scripts/configure_codex.py` para vincular Codex con CodeBridge y muéstrame las variables de entorno configuradas.
```

---

## 🚀 Lanzador Corto y Skill MCP (`cbm`)

CodeBridge incluye un lanzador simplificado para la terminal y una habilidad para agentes:

### Comandos de Terminal (`cb`):
```bash
./scripts/cb mcp     # Verifica/Arranca CodeBridge en 2do plano y muestra estado/token
./scripts/cb logs    # Ver logs del servidor en tiempo real
./scripts/cb stop    # Detener el servidor
```

### Habilidad para Agentes (`cbm`):
Invocable dentro del entorno del agente usando la palabra clave **`cbm`** (Skill: `cbm` / `codebridge-mcp`).

---

## 📚 Guías Detalladas de la Comunidad

- 📖 **[Guía de Instalación Detallada](docs/GUIA_INSTALACION_ES.md)**
- 🧠 **[Modelos Recomendados de NVIDIA NIM](docs/MODELOS_RECOMENDADOS.md)**
- 🛠️ **[Solución de Problemas y FAQ](docs/SOLUCION_PROBLEMAS.md)**

---

## 🛡️ Seguridad

- **Host Local Únicamente:** Gateway configurado en `127.0.0.1`.
- **Aislamiento de Secretos:** Tu `NVIDIA_API_KEY` nunca sale hacia Codex ni se muestra en los logs.
- **Redacción de Logs:** Eliminación automática de credenciales en `codebridge_server.log`.

---

## 📄 Licencia

MIT — Consulta [LICENSE](LICENSE) para más detalles.
