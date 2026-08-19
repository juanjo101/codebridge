---
name: cbm-map
description: Habilidad de mapeo de contexto para CodeBridge. Proporciona a NVIDIA NIM conocimiento espacial del proyecto.
---

# Map-Reduce Contextual

Esta habilidad se ejecuta automáticamente cuando el usuario invoca `cbm`.

1. Un script (`scripts/generate_map.py`) lee la estructura del directorio.
2. Extrae las firmas de todas las clases y funciones de Python.
3. Lo guarda en `.cbm_project_map.txt`.
4. El script `query_cbm.py` lee este mapa y lo adjunta al prompt del usuario para que NVIDIA NIM sepa exactamente en qué archivos están definidas las cosas.
