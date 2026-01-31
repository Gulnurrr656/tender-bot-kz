import json
from pathlib import Path
from typing import Set

CHATS_PATH = Path(__file__).parents[1] / "db" / "chats.json"


def load_chats() -> Set[int]:
    if not CHATS_PATH.exists():
        return set()

    with open(CHATS_PATH, "r", encoding="utf-8") as f:
        try:
            return set(map(int, json.load(f)))
        except json.JSONDecodeError:
            return set()


def save_chats(chat_ids: Set[int]) -> None:
    CHATS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CHATS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(chat_ids), f, ensure_ascii=False, indent=2)
