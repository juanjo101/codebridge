# 🧠 Guía de Modelos Recomendados de NVIDIA NIM para Programar

NVIDIA NIM ofrece acceso a docenas de los mejores modelos de lenguaje del mundo. CodeBridge te permite utilizarlos transparentemente para tus tareas de desarrollo de software diario.

En esta guía te recomendamos los mejores modelos según el tipo de tarea y cómo configurarlos.

---

## 🏆 Modelos Destacados para Programación

| Modelo | Especialidad | Velocidad | Contexto | Cuándo Usarlo |
| :--- | :--- | :--- | :--- | :--- |
| **`meta/llama-3.3-70b-instruct`** *(Recomendado por Defecto)* | Todo propósito, código complejo, arquitectura, refactorización masiva | ⚡⚡⚡ Rápido | 128k tokens | **Tu modelo principal.** Excelente en lógica, Python, JS/TS, Rust, Go, SQL y resolución de bugs. |
| **`nvidia/llama-3.1-nemotron-70b-instruct`** | Razonamiento profundo y resolución de problemas complejos | ⚡⚡ Moderado | 128k tokens | Ideal para tareas que requieren analizar arquitectura compleja o lógica pesada. |
| **`deepseek-ai/deepseek-coder-7b-instruct-v1.5`** | Autocompletado y funciones de código pequeñas | ⚡⚡⚡⚡ Ultra Rápido | 16k tokens | Ideal para generar scripts rápidos, snippets y respuestas ultra ágiles. |
| **`meta/llama-3.2-3b-instruct`** / **`meta/llama-3.2-11b-vision-instruct`** | Tareas ligeras / Análisis multimodal | ⚡⚡⚡⚡ Ultra Rápido | 128k tokens | Documentación, generación de READMEs, formateo y análisis rápido. |

---

## ⚙️ Cómo Cambiar el Modelo en CodeBridge

### 1. Ver todos los modelos disponibles en tu cuenta

Ejecuta el siguiente comando para ver la lista en tiempo real directamente desde NVIDIA:

```bash
uv run codebridge models
```

### 2. Establecer el modelo por defecto en `.env`

Edita tu archivo `.env` en la raíz de CodeBridge:

```env
# .env
NVIDIA_DEFAULT_MODEL=meta/llama-3.3-70b-instruct
```

### 3. Establecer el modelo específico en Codex

También puedes definir el modelo directamente en la configuración de Codex (`~/.codex/config.toml`):

```toml
model_provider = "codebridge"
model = "meta/llama-3.3-70b-instruct"
```

---

## 💡 Estrategia de Trabajo: Modo Economía vs. Modo Premium

Para maximizar tu productividad y minimizar gastos de tokens:

### 🟢 Modo Economía (CodeBridge + NVIDIA NIM)
Configura `model_provider = "codebridge"` en Codex.

**Úsalo para el 90% de tus tareas diarias:**
- Escribir funciones, endpoints API y componentes UI.
- Generar tests unitarios e integración.
- Refactorización de código y formateo.
- Explicar código legacy y escribir documentación.
- Crear scripts y consultas SQL.

### 🔵 Modo Premium (OpenAI Directo / Claude)
Configura `model_provider = "openai"` en Codex.

**Resérvalo para:**
- Decisiones arquitectónicas críticas de todo el proyecto.
- Debugging extremo en sistemas distribuidos complejos.
- Auditorías de seguridad avanzadas.

---

## ❓ Preguntas Frecuentes sobre Modelos

### ¿Los modelos de NVIDIA soportan Tool Calling / Function Calling?
Sí, la mayoría de modelos como `meta/llama-3.3-70b-instruct` soportan la llamada a herramientas (*tool calling*) sin problemas a través del adaptador de CodeBridge.

### ¿Puedo probar varios modelos sin reiniciar el servidor?
¡Sí! Solo cambia la propiedad `model` en la petición o en `~/.codex/config.toml` y CodeBridge enrutará la petición al modelo correspondiente en NVIDIA.
