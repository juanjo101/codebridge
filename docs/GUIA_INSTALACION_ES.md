# 🚀 Guía de Instalación Rápida de CodeBridge

¡Bienvenido! En esta guía aprenderás a instalar y configurar **CodeBridge** en menos de 5 minutos en tu entorno de desarrollo local.

CodeBridge te permite conectar **Codex** y tus herramientas de IA locales con los modelos de **NVIDIA NIM** (como Llama 3.3 70B, DeepSeek Coder, Nemotron, etc.), permitiéndote programar diariamente sin consumir créditos de pago.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de contar con:

1. **Python 3.10 o superior** instalado (`python3 --version` o `python --version`).
2. **Git** (`git --version`).
3. **Una clave de API de NVIDIA** (Gratuita).

---

## 🔑 Paso 1: Obtener tu API Key gratuita de NVIDIA

1. Ve a [NVIDIA Build Catalog](https://build.nvidia.com).
2. Haz clic en **Sign In** e inicia sesión (puedes usar tu cuenta de Google, GitHub o correo).
3. Entra a la sección de **API Keys** o genera una nueva clave desde cualquier modelo en la plataforma.
4. Copia tu clave (comienza por `nvapi-...`).

> 💡 **Nota:** NVIDIA te otorga créditos gratuitos para probar y usar sus modelos en desarrollo.

---

## 🛠️ Paso 2: Descargar e Instalar CodeBridge

Abre tu terminal o PowerShell y ejecuta los siguientes comandos:

### 🐧 Linux / 🍎 macOS

```bash
# 1. Clonar el repositorio
git clone https://github.com/juanjo101/codebridge.git
cd codebridge

# 2. Ejecutar script de instalación automática
bash scripts/setup.sh
```

### 🪟 Windows (PowerShell)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/juanjo101/codebridge.git
cd codebridge

# 2. Ejecutar el script de instalación (abrir PowerShell como Administrador si es necesario)
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

> El script instalará `uv` (administrador ultrarrápido de entornos Python), creará el entorno virtual e instalará las dependencias necesarias.

---

## ⚙️ Paso 3: Configurar la API Key de NVIDIA

Abre el archivo `.env` en la raíz del proyecto (creado automáticamente a partir de `.env.example`) y pega tu API Key de NVIDIA:

```env
# .env
NVIDIA_API_KEY=nvapi-tu-clave-aqui
```

---

## ▶️ Paso 4: Iniciar CodeBridge y Verificar Conexión

### 1. Iniciar el Servidor Gateway

```bash
# En Linux / macOS
./scripts/start.sh

# En Windows PowerShell
.\scripts\start.ps1

# O directamente mediante el CLI de CodeBridge
uv run codebridge serve
```

Verás una salida indicando que CodeBridge está corriendo en `http://127.0.0.1:8787`.

### 2. Probar la Conexión con NVIDIA

En otra pestaña de la terminal, ejecuta la prueba de conectividad automática:

```bash
python scripts/test_nvidia.py
```

Deberías ver un resultado exitoso similar a este:
```text
NVIDIA CONNECTION TEST
==================================================
[1/6] Checking NVIDIA API... PASS (101 models)
[2/6] Fetching models... PASS (101 models)
[3/6] Testing basic response... PASS
[4/6] Testing streaming... PASS
[5/6] Testing tool calling... PASS
```

---

## 🔌 Paso 5: Conectar Codex a CodeBridge

Puedes configurar **Codex** automáticamente ejecutando:

```bash
uv run python scripts/configure_codex.py
```

O si prefieres hacerlo manualmente, edita tu archivo `~/.codex/config.toml`:

```toml
model_provider = "codebridge"
model = "meta/llama-3.3-70b-instruct"

[model_providers.codebridge]
name = "CodeBridge NVIDIA"
base_url = "http://127.0.0.1:8787/v1"
env_key = "CODEBRIDGE_LOCAL_TOKEN"
wire_api = "responses"
```

Asegúrate de exportar tu token local de seguridad antes de usar Codex:

```bash
export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
```

---

## 🎮 Comandos Útiles del CLI

| Comando | Descripción |
| :--- | :--- |
| `uv run codebridge serve` | Inicia el Gateway servidor en segundo plano/terminal |
| `uv run codebridge models` | Lista todos los modelos disponibles en tu cuenta de NVIDIA |
| `uv run codebridge health` | Muestra el estado de salud del servicio |
| `uv run codebridge test` | Realiza un test de conexión completo a NVIDIA NIM |
| `uv run codebridge token` | Muestra el token de autenticación local |
| `uv run codebridge usage` | Muestra las estadísticas locales de uso de tokens |

---

## 🎯 ¿Qué sigue?

- Revisa nuestra [Guía de Modelos Recomendados](MODELOS_RECOMENDADOS.md) para saber cuál elegir según tu proyecto.
- Si encuentras algún inconveniente, consulta la [Guía de Solución de Problemas](SOLUCION_PROBLEMAS.md).
