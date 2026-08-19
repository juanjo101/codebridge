#!/usr/bin/env bash
''':'
exec uv run python "$0" "$@"
'''
"""
query_cbm.py — Utility to send coding tasks directly to CodeBridge Gateway (NVIDIA NIM).
"""

import sys
import json
import urllib.request
from pathlib import Path

def query_codebridge(prompt: str, model: str = None) -> str:
    token_file = Path(__file__).parent.parent / ".codebridge_token"
    if not token_file.exists():
        token_file = Path.home() / ".codebridge_token"
    
    token = token_file.read_text().strip() if token_file.exists() else "FP48A58AloNP9QcOjA0csi3awTg1zT_LaLAha2DqCKM"
    
    HISTORY_FILE = Path(__file__).parent.parent / ".cbm_history.json"
    
    # Load history
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            pass

    # Append new user prompt
    history.append({"role": "user", "content": prompt})

    import subprocess

    # 1. Update Project Map
    map_script = Path(__file__).parent / "generate_map.py"
    if map_script.exists():
        try:
            subprocess.run([sys.executable, str(map_script)], check=False)
        except Exception:
            pass

    system_instructions = "Eres un asistente de programación experto impulsado por NVIDIA NIM a través de CodeBridge Gateway. Responde con soluciones técnicas de alta calidad en español."
    
    # 2. Inject Project Map
    map_file = Path(__file__).parent.parent / ".cbm_project_map.txt"
    if map_file.exists():
        try:
            map_data = map_file.read_text(encoding="utf-8")
            system_instructions += f"\n\n--- CONTEXTO DEL PROYECTO (MAPA) ---\n{map_data[:5000]}\n--- FIN DEL MAPA ---\n"
        except Exception:
            pass

    # 3. Inject UI/UX rules if keyword matches
    prompt_lower = prompt.lower()
    ux_keywords = ["ui", "ux", "frontend", "diseño", "pantalla", "interfaz", "css", "html", "react"]
    if any(k in prompt_lower for k in ux_keywords):
        ui_skill_file = Path(__file__).parent.parent / ".agents" / "skills" / "cbm-ui-ux" / "SKILL.md"
        if ui_skill_file.exists():
            try:
                ui_data = ui_skill_file.read_text(encoding="utf-8")
                system_instructions += f"\n\n--- REGLAS UI/UX OBLIGATORIAS ---\n{ui_data}\n--- FIN REGLAS UI/UX ---\n"
            except Exception:
                pass

    payload = {
        "instructions": system_instructions,
        "input": history
    }
    if model:
        payload["model"] = model

    req = urllib.request.Request(
        "http://127.0.0.1:8787/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result_text = json.dumps(data, indent=2)
            
            # Prefer top-level output_text if available
            if "output_text" in data and data["output_text"]:
                result_text = data["output_text"]
            # Fallback to parsing the output list
            elif "output" in data and isinstance(data["output"], list):
                chunks = []
                for item in data["output"]:
                    if isinstance(item, dict) and "content" in item:
                        for content_item in item["content"]:
                            if content_item.get("type") in ("text", "output_text"):
                                chunks.append(content_item.get("text", ""))
                result_text = "".join(chunks)

            # Save history
            history.append({"role": "assistant", "content": result_text})
            try:
                with open(HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=2)
            except Exception:
                pass

            return result_text
    except Exception as e:
        return f"Error conectando a CodeBridge (http://127.0.0.1:8787): {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/query_cbm.py 'tu prompt o tarea de código'")
        sys.exit(1)
    prompt_arg = " ".join(sys.argv[1:])
    response = query_codebridge(prompt_arg)
    print(response)
