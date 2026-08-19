#!/usr/bin/env python3
"""
generate_map.py — Generates a project context map for CodeBridge Gateway.
"""

import os
import ast
from pathlib import Path

def get_python_signatures(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read())
        
        signatures = []
        for item in node.body:
            if isinstance(item, ast.ClassDef):
                signatures.append(f"class {item.name}:")
                for sub in item.body:
                    if isinstance(sub, ast.FunctionDef):
                        signatures.append(f"    def {sub.name}(...)")
            elif isinstance(item, ast.FunctionDef):
                signatures.append(f"def {item.name}(...)")
        return signatures
    except Exception:
        return []

def generate_map(root_dir, output_file):
    root = Path(root_dir)
    lines = ["# PROJECT CONTEXT MAP", ""]
    
    ignore_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.agents', '.pytest_cache', '.ruff_cache'}
    ignore_exts = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.db', '.sqlite3'}
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        rel_path = Path(dirpath).relative_to(root)
        if rel_path == Path('.'):
            rel_str = "/"
        else:
            rel_str = f"/{rel_path}"
            
        lines.append(f"Directory: {rel_str}")
        
        for file in sorted(filenames):
            if Path(file).suffix in ignore_exts:
                continue
            
            full_path = Path(dirpath) / file
            lines.append(f"  - {file}")
            
            if file.endswith('.py'):
                sigs = get_python_signatures(full_path)
                if sigs:
                    lines.append("      Symbols:")
                    for sig in sigs:
                        lines.append(f"        {sig}")
        lines.append("")
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    generate_map(Path.cwd(), Path.cwd() / ".cbm_project_map.txt")
