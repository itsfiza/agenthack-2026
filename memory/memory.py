import json
import os
from typing import Dict, Any, List


MEMORY_FILE = "memory/pipeline_memory.json"


def _ensure_memory_file():
    """
    Create the memory directory and JSON file if they don't exist.
    """

    os.makedirs("memory", exist_ok=True)

    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "leads": {},
                    "interactions": []
                },
                f,
                indent=2
            )


def load_memory() -> Dict[str, Any]:
    """
    Load persistent pipeline memory.
    """

    _ensure_memory_file()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {
            "leads": {},
            "interactions": []
        }


def save_memory(memory: Dict[str, Any]):
    """
    Save pipeline memory.
    """

    _ensure_memory_file()

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            memory,
            f,
            indent=2,
            ensure_ascii=False
        )


def remember_lead(
    company: str,
    lead_data: Dict[str, Any]
):
    """
    Store or update a lead in persistent memory.
    """

    memory = load_memory()

    memory["leads"][company] = lead_data

    save_memory(memory)


def remember_interaction(
    company: str,
    interaction: Dict[str, Any]
):
    """
    Store an interaction with a lead.
    """

    memory = load_memory()

    interaction_record = {
        "company": company,
        **interaction
    }

    memory["interactions"].append(
        interaction_record
    )

    save_memory(memory)


def get_lead_memory(
    company: str
) -> Dict[str, Any]:

    memory = load_memory()

    return memory.get(
        "leads",
        {}
    ).get(
        company,
        {}
    )


def get_all_leads() -> Dict[str, Any]:

    memory = load_memory()

    return memory.get(
        "leads",
        {}
    )


def get_interactions() -> List[Dict[str, Any]]:

    memory = load_memory()

    return memory.get(
        "interactions",
        []
    )