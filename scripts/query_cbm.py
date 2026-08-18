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
    
    payload = {
        "instructions": "Eres un asistente de programación experto impulsado por NVIDIA NIM a través de CodeBridge Gateway. Responde con soluciones técnicas de alta calidad en español.",
        "input": prompt
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
            # Prefer top-level output_text if available
            if "output_text" in data and data["output_text"]:
                return data["output_text"]
            
            # Fallback to parsing the output list
            if "output" in data and isinstance(data["output"], list):
                chunks = []
                for item in data["output"]:
                    if isinstance(item, dict) and "content" in item:
                        for content_item in item["content"]:
                            # Both 'text' and 'output_text' might be used
                            if content_item.get("type") in ("text", "output_text"):
                                chunks.append(content_item.get("text", ""))
                return "".join(chunks)
            
            return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error conectando a CodeBridge (http://127.0.0.1:8787): {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/query_cbm.py 'tu prompt o tarea de código'")
        sys.exit(1)
    prompt_arg = " ".join(sys.argv[1:])
    response = query_codebridge(prompt_arg)
    print(response)
