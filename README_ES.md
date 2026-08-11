# 🌉 CodeBridge Gateway

> **Gateway local ligero que conecta tu entorno de desarrollo (Codex) con los modelos de NVIDIA NIM.**

[![Licencia MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Soporte Bilingüe](https://img.shields.io/badge/Docs-Español%20%7C%20English-orange.svg)](#-documentación)

[ English Version ](README.md) | **[ versión en Español ](README_ES.md)**

```text
Codex / Cliente OpenAI  ──►  Responses API  ──►  CodeBridge  ──►  NVIDIA NIM (Chat Completions)
```

---

## ⚡ ¿Qué es CodeBridge y por qué lo necesitas?

**CodeBridge** te permite utilizar la potencia de los modelos de inteligencia artificial de **NVIDIA NIM** (como Llama 3.3 70B, DeepSeek Coder, Nemotron) directamente desde **Codex** y tus asistentes de desarrollo locales.

### 💰 Tu Modo Economía para Programar
En lugar de gastar créditos de APIs de pago en tareas rutinarias del día a día, **CodeBridge enruta tus peticiones de código a los modelos de NVIDIA NIM**, reservando las APIs de pago únicamente para arquitectura compleja o tareas críticas.

---

## 📐 Arquitectura

```text
┌──────────────────────────────────────────────────────────┐
│  Codex / Cliente IDE                                    │
│  (Envía peticiones en formato OpenAI Responses API)       │
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

## 🚀 Inicio Rápido (En 3 Pasos)

### 1. Clonar e Instalar

```bash
# Linux / macOS
git clone https://github.com/juanjo101/codebridge.git
cd codebridge
bash scripts/setup.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/juanjo101/codebridge.git
cd codebridge
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

### 2. Configurar tu API Key de NVIDIA

Crea o edita tu archivo `.env` en la raíz de CodeBridge con tu clave gratuita de [NVIDIA Build](https://build.nvidia.com):

```env
NVIDIA_API_KEY=nvapi-tu-clave-aqui
```

### 3. Iniciar CodeBridge y Probar

```bash
# Iniciar el servidor
./scripts/start.sh

# Probar la conexión (en otra terminal)
python scripts/test_nvidia.py
```

---

## 📚 Enlaces a la Documentación Completa

Hemos preparado guías detalladas para que puedas aprovechar al máximo CodeBridge:

- 📖 **[Guía de Instalación Detallada Paso a Paso](docs/GUIA_INSTALACION_ES.md)**
- 🧠 **[Modelos Recomendados para Programación](docs/MODELOS_RECOMENDADOS.md)**
- 🛠️ **[Solución de Problemas y FAQ](docs/SOLUCION_PROBLEMAS.md)**

---

## 🔌 Conectar Codex a CodeBridge

Configura Codex automáticamente ejecutando:

```bash
uv run python scripts/configure_codex.py
```

O añade manualmente la configuración a tu `~/.codex/config.toml`:

```toml
model_provider = "codebridge"
model = "meta/llama-3.3-70b-instruct"

[model_providers.codebridge]
name = "CodeBridge NVIDIA"
base_url = "http://127.0.0.1:8787/v1"
env_key = "CODEBRIDGE_LOCAL_TOKEN"
wire_api = "responses"
```

Exporta la clave de autenticación local:
```bash
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

---

## 🛡️ Seguridad Garantizada

- **Solo Localhost:** CodeBridge escucha por defecto únicamente en `127.0.0.1`.
- **Aislamiento de Claves:** Codex nunca tiene acceso a tu clave `NVIDIA_API_KEY`.
- **Redacción de Secretos:** Todas las claves, tokens y encabezados de autorización son redactados automáticamente de los logs.
- **Sin Telemetría Externa:** Tus métricas y logs permanecen 100% en tu máquina local.

---

## 🛠️ Comandos del CLI de CodeBridge

```text
codebridge serve           Inicia el servidor Gateway
codebridge health          Muestra el estado de salud de CodeBridge
codebridge models          Lista los modelos disponibles en tu cuenta NVIDIA
codebridge test            Ejecuta el test de conectividad completo a NVIDIA
codebridge usage           Muestra estadísticas de uso de tokens locales
codebridge token           Muestra el token de autenticación local
codebridge configure-codex Configura automáticamente Codex
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT** — consulta el archivo [LICENSE](LICENSE) para más detalles.
