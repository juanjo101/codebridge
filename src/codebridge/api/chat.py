"""
GET /chat — Web GUI Chat Interface for CodeBridge.

Provides a modern Single Page Application (SPA) to chat and generate code
visually using NVIDIA NIM models through CodeBridge Gateway.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_CHAT_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CodeBridge Gateway — Chat GUI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <style>
    :root {
      --bg-dark: #0f172a;
      --bg-card: rgba(30, 41, 59, 0.7);
      --bg-sidebar: #1e293b;
      --border-color: rgba(255, 255, 255, 0.1);
      --accent-primary: #6366f1;
      --accent-hover: #4f46e5;
      --accent-green: #10b981;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --user-msg-bg: #334155;
      --assistant-msg-bg: rgba(30, 41, 59, 0.9);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    header {
      background-color: var(--bg-sidebar);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .logo-container {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .logo-icon {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #6366f1, #10b981);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: white;
    }
    .logo-title {
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: rgba(16, 185, 129, 0.1);
      color: var(--accent-green);
      font-size: 0.8rem;
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      background-color: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
    }
    .header-controls {
      display: flex;
      gap: 16px;
      align-items: center;
    }
    select, input {
      background-color: var(--bg-dark);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }
    select:focus, input:focus {
      border-color: var(--accent-primary);
    }
    .main-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      max-width: 1000px;
      width: 100%;
      margin: 0 auto;
      height: calc(100vh - 65px);
      padding: 16px;
      gap: 16px;
    }
    .chat-history {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      border-radius: 12px;
      background: var(--bg-card);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border-color);
    }
    .message {
      display: flex;
      gap: 12px;
      max-width: 85%;
      animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }
    .message.assistant {
      align-self: flex-start;
    }
    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      font-weight: 600;
      flex-shrink: 0;
    }
    .message.user .avatar {
      background: var(--accent-primary);
      color: white;
    }
    .message.assistant .avatar {
      background: linear-gradient(135deg, #10b981, #06b6d4);
      color: white;
    }
    .bubble {
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 0.95rem;
      line-height: 1.5;
    }
    .message.user .bubble {
      background-color: var(--user-msg-bg);
      border-top-right-radius: 2px;
    }
    .message.assistant .bubble {
      background-color: var(--assistant-msg-bg);
      border: 1px solid var(--border-color);
      border-top-left-radius: 2px;
      width: 100%;
    }
    .bubble pre {
      background-color: #090d16;
      border-radius: 8px;
      padding: 12px;
      margin: 10px 0;
      overflow-x: auto;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .bubble code {
      font-family: 'Fira Code', monospace;
      font-size: 0.88rem;
    }
    .input-area {
      display: flex;
      gap: 12px;
      background: var(--bg-card);
      padding: 12px;
      border-radius: 12px;
      border: 1px solid var(--border-color);
    }
    textarea {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.95rem;
      resize: none;
      outline: none;
      height: 48px;
      max-height: 150px;
    }
    button.send-btn {
      background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
      color: white;
      border: none;
      padding: 0 24px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.1s ease, opacity 0.2s ease;
    }
    button.send-btn:hover {
      opacity: 0.95;
      transform: translateY(-1px);
    }
    button.send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #1e293b;
      padding: 4px 10px;
      border-top-left-radius: 6px;
      border-top-right-radius: 6px;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .copy-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 2px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.7rem;
    }
    .copy-btn:hover {
      color: white;
      border-color: white;
    }
  </style>
</head>
<body>

  <header>
    <div class="logo-container">
      <div class="logo-icon">CB</div>
      <div>
        <div class="logo-title">CodeBridge Web Chat</div>
        <div style="font-size: 0.75rem; color: var(--text-muted)">Conectado a NVIDIA NIM</div>
      </div>
    </div>
    <div class="header-controls">
      <div class="status-badge">
        <span class="status-dot"></span> Gateway Online (127.0.0.1:8787)
      </div>
      <select id="model-select">
        <option value="meta/llama-3.3-70b-instruct">meta/llama-3.3-70b-instruct</option>
        <option value="nvidia/llama-3.1-nemotron-70b-instruct">nvidia/llama-3.1-nemotron-70b-instruct</option>
        <option value="deepseek-ai/deepseek-coder-6.7b-instruct">deepseek-ai/deepseek-coder-6.7b-instruct</option>
      </select>
    </div>
  </header>

  <div class="main-container">
    <div class="chat-history" id="chat-history">
      <div class="message assistant">
        <div class="avatar">NIM</div>
        <div class="bubble">
          👋 <strong>¡Bienvenido a CodeBridge Web Chat!</strong><br><br>
          Esta interfaz gráfica te permite chatear y pedir código directamente procesado por las GPUs de <strong>NVIDIA NIM</strong> sin gastar cuotas ni usar la terminal.<br><br>
          Escribe tu consulta o pide un script abajo para comenzar.
        </div>
      </div>
    </div>

    <div class="input-area">
      <textarea id="prompt-input" placeholder="Escribe tu consulta o pide código aquí... (Shift+Enter para nueva línea)"></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()">Enviar</button>
    </div>
  </div>

  <script>
    const token = "FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM";
    const history = document.getElementById("chat-history");
    const input = document.getElementById("prompt-input");
    const sendBtn = document.getElementById("send-btn");

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    async function loadModels() {
      try {
        const res = await fetch("/v1/models");
        if (res.ok) {
          const data = await res.json();
          const select = document.getElementById("model-select");
          if (data.data && data.data.length > 0) {
            select.innerHTML = "";
            data.data.forEach(m => {
              const opt = document.createElement("option");
              opt.value = m.id;
              opt.textContent = m.id;
              if (m.id === "meta/llama-3.3-70b-instruct") opt.selected = true;
              select.appendChild(opt);
            });
          }
        }
      } catch (err) { console.log("Models load fallback"); }
    }
    loadModels();

    function appendMessage(role, text) {
      const msgDiv = document.createElement("div");
      msgDiv.className = `message ${role}`;
      
      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = role === "user" ? "Tú" : "NIM";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.innerHTML = formatMarkdown(text);

      msgDiv.appendChild(avatar);
      msgDiv.appendChild(bubble);
      history.appendChild(msgDiv);
      history.scrollTop = history.scrollHeight;

      // Highlight code blocks
      msgDiv.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));
      return bubble;
    }

    function formatMarkdown(str) {
      if (!str) return "";
      // Simple code block formatting
      let html = str.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'plaintext'}">${escapeHtml(code.trim())}</code></pre>`;
      });
      return html.replace(/\\n/g, "<br>");
    }

    function escapeHtml(text) {
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      const model = document.getElementById("model-select").value;
      input.value = "";
      sendBtn.disabled = true;

      appendMessage("user", text);
      const assistantBubble = appendMessage("assistant", "⚡ Pensando...");

      try {
        const res = await fetch("/v1/responses", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            model: model,
            input: [{ role: "user", content: [{ type: "input_text", text: text }] }]
          })
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        const replyText = data.output_text || (data.output && data.output[0] && data.output[0].content[0].text) || "Respuesta completada sin texto.";
        assistantBubble.innerHTML = formatMarkdown(replyText);
        assistantBubble.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));

      } catch (err) {
        assistantBubble.innerHTML = `<span style="color: #ef4444">Error al conectar con CodeBridge Gateway: ${err.message}</span>`;
      } finally {
        sendBtn.disabled = false;
        history.scrollTop = history.scrollHeight;
      }
    }
  </script>
</body>
</html>
"""


@router.get("/chat", response_class=HTMLResponse)
async def get_chat_ui() -> HTMLResponse:
    """Render the CodeBridge Web GUI Chat interface."""
    return HTMLResponse(content=_CHAT_HTML)


@router.get("/", response_class=HTMLResponse)
async def get_root() -> HTMLResponse:
    """Redirect root endpoint to Web GUI Chat."""
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
      <meta http-equiv="refresh" content="0; url=/chat">
    </head>
    <body>
      <p>Redirecting to <a href="/chat">CodeBridge Chat GUI</a>...</p>
    </body>
    </html>
    """
    )
