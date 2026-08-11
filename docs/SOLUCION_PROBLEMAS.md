# 🛠️ Solución de Problemas y Preguntas Frecuentes (FAQ)

Si experimentas problemas al instalar, configurar o usar **CodeBridge**, aquí encontrarás las soluciones a las situaciones más comunes.

---

## 🔍 Diagnóstico Rápido de 3 Pasos

Antes de revisar problemas específicos, ejecuta estas 3 verificaciones básicas:

### 1. Comprobar la salud del Gateway
```bash
uv run codebridge health
# o
curl http://127.0.0.1:8787/health
```
*Si responde `{"status":"ok", ...}`, el servidor local está funcionando correctamente.*

### 2. Probar la conexión con NVIDIA
```bash
uv run codebridge test
# o
python scripts/test_nvidia.py
```
*Verifica que tu clave `NVIDIA_API_KEY` sea válida y pueda listar modelos.*

### 3. Inspeccionar el Informe de Diagnóstico
```bash
curl "http://127.0.0.1:8787/diagnostics?format=text"
```

---

## ❌ Problemas Frecuentes y Soluciones

### 1. Error `401 Unauthorized` desde Codex o `curl`

**Causa:** El token local enviado no coincide con el token generado por CodeBridge.

**Solución:**
1. Muestra tu token local registrado ejecutando:
   ```bash
   uv run codebridge token
   ```
2. Asegúrate de exportar la variable de entorno en la terminal donde ejecutas Codex:
   ```bash
   export CODEBRIDGE_LOCAL_TOKEN=$(cat .codebridge_token)
   ```
3. Verifica que tu `~/.codex/config.toml` contenga:
   ```toml
   env_key = "CODEBRIDGE_LOCAL_TOKEN"
   ```

---

### 2. Error `El puerto 8787 ya está en uso`

**Causa:** Otra instancia de CodeBridge u otro proceso local está usando el puerto 8787.

**Solución:**
- En Linux / macOS:
  ```bash
  # Buscar el proceso en el puerto 8787
  lsof -i :8787
  # O detener la instancia previa
  pkill -f codebridge
  ```
- En Windows (PowerShell):
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8787).OwningProcess | Stop-Process
  ```

---

### 3. Error `401 / 403 API Key Invalid` desde NVIDIA

**Causa:** Tu clave `NVIDIA_API_KEY` en el archivo `.env` es incorrecta o no ha sido cargada.

**Solución:**
1. Revisa tu archivo `.env` y confirma que la clave empiece por `nvapi-`:
   ```env
   NVIDIA_API_KEY=nvapi-XXXXXX...
   ```
2. Recuerda no incluir comillas ni espacios extra alrededor de la clave.
3. Genera una nueva clave si es necesario en [build.nvidia.com](https://build.nvidia.com).

---

### 4. Error `404 Model Not Found`

**Causa:** El modelo especificado en `NVIDIA_DEFAULT_MODEL` o en Codex no está disponible en la API de NVIDIA NIM.

**Solución:**
1. Consulta la lista exacta de modelos disponibles para tu cuenta:
   ```bash
   uv run codebridge models
   ```
2. Actualiza tu `.env` o `~/.codex/config.toml` con un nombre de modelo válido de la lista (por ejemplo `meta/llama-3.3-70b-instruct`).

---

### 5. El Streaming se interrumpe o muestra texto parcial

**Causa:** Problemas de buffering en clientes HTTP o configuración de la fallback API.

**Solución:**
- Asegúrate de que `CODEBRIDGE_RESPONSES_FALLBACK=true` en tu archivo `.env`.
- Revisa el archivo de log para identificar posibles timeouts de red:
  ```bash
  tail -f codebridge_server.log
  ```

---

## 🪵 Cómo Consultar los Logs

CodeBridge incluye redacción automática de secretos en los logs. Puedes revisar los registros de ejecución en cualquier momento:

```bash
# Ver los últimos logs en tiempo real
tail -n 50 -f codebridge_server.log
```

---

## 💬 ¿Sigues teniendo dudas?

Si continúas con problemas:
1. Abre un *Issue* en el repositorio de GitHub adjuntando el resultado de `uv run codebridge test`.
2. Revisa que estés utilizando la última versión de CodeBridge (`git pull origin main`).
