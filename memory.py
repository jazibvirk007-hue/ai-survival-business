import json
import os


MEMORY_FILE = "ai_memory.json"


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)

    except Exception:
        return []


def save_memory(memory):

    with open(MEMORY_FILE, "w") as file:

        json.dump(
            memory,
            file,
            indent=4
        )


def add_memory(event):

    memory = load_memory()

    memory.append(event)

    save_memory(memory)

    return memory