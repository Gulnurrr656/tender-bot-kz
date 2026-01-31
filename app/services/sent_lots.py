# app/services/sent_lots.py

import json
from pathlib import Path
from typing import Set

SENT_LOTS_PATH = Path(__file__).parents[1] / "db" / "sent_lots.json"


def load_sent_lots() -> Set[str]:
    if not SENT_LOTS_PATH.exists():
        return set()

    try:
        with open(SENT_LOTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(map(str, data))
    except Exception:
        return set()


def save_sent_lots(sent_keys: Set[str]) -> None:
    SENT_LOTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(SENT_LOTS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            sorted(sent_keys),
            f,
            ensure_ascii=False,
            indent=2
        )
