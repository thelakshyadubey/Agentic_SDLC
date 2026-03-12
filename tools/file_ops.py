import os
from typing import List
WORKSPACE_DIR = "generated_workspace"

def write_file(filename: str, content: str) -> str:
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    filepath = os.path.join(WORKSPACE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote {filepath}"

def read_file(filename: str) -> str:
    filepath = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(filepath):
        return f"File {filepath} does not exist."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def list_files() -> List[str]:
    if not os.path.exists(WORKSPACE_DIR):
        return []
    return os.listdir(WORKSPACE_DIR)
