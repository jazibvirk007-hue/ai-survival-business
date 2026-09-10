import json
import os


MEMORY_FILE = "ai_memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def save_memory(memory):
    if not isinstance(memory, list):
        raise TypeError("memory must be a list")
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4, ensure_ascii=False)


def add_memory(event):
    memory = load_memory()
    memory.append(event)
    save_memory(memory)
    return memory
