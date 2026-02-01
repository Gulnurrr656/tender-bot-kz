import json
from pathlib import Path
from typing import Set, Dict

SENT_LOTS_PATH = Path(__file__).parents[1] / "db" / "sent_lots.json"
USER_SEEN_PATH = Path(__file__).parents[1] / "db" / "user_seen_lots.json"


# ─────────────────────────
# ГЛОБАЛЬНЫЕ ЛОТЫ (как было)
# ─────────────────────────

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


# ─────────────────────────
# 👤 PER-USER (для pagination)
# ─────────────────────────

def load_user_seen() -> Dict[str, Set[str]]:
    """
    { chat_id: {lot_key, lot_key, ...} }
    """
    if not USER_SEEN_PATH.exists():
        return {}

    try:
        with open(USER_SEEN_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return {
                str(chat_id): set(map(str, lots))
                for chat_id, lots in raw.items()
            }
    except Exception:
        return {}


def save_user_seen(data: Dict[str, Set[str]]) -> None:
    USER_SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    serializable = {
        chat_id: sorted(lots)
        for chat_id, lots in data.items()
    }

    with open(USER_SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(
            serializable,
            f,
            ensure_ascii=False,
            indent=2
        )
