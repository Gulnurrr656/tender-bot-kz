# app/services/lot_filter.py

KEYWORDS = [
    # ───────── ОДЕЖДА / ТОВАРЫ ─────────
    "курт",
    "халат",
    "спец",
    "одежд",
    "форма",
    "обмундир",
    "комбинезон",
    "бахил",
    "перчат",
    "маск",
    "матрас",
    "постель",
    "подушк",
    "одеял",
    "полотенц",
    "однораз",
    "белье",

    # ───────── РАБОТЫ ─────────
    "ремонт",
    "монтаж",
    "установ",
    "строит",
    "отделоч",
    "реконструкц",
    "техническ",

    # ───────── УСЛУГИ / ПОСТАВКИ ─────────
    "поставка",
    "поставк",
    "обслуживан",
    "сопровожд",
    "оказан",
    "аренд",
    "услуг",

    # ───────── IT / ЦИФРОВИЗАЦИЯ ─────────
    "сайт",
    "веб",
    "web",
    "портал",
    "информацион",
    "автоматизац",
    "цифров",
    "система",
    "ис ",
    "разработ",
    "создан",
    "модернизац",
    "программ",
    "по ",
    "software",
    "мобильн",
    "приложен",
    "поддержк",
    "сопровожд",
    "техподдерж",
    "интеграц",
    "сервер",
    "база данн",
]


def get_status_text(lot: dict) -> str:
    """
    Пытаемся достать статус из всех возможных полей
    """
    return (
        lot.get("status_name_ru")
        or lot.get("ref_lot_status_name_ru")
        or lot.get("lotStatus", {}).get("nameRu")
        or ""
    ).lower()


def is_open_lot(lot: dict) -> bool:
    status = get_status_text(lot)
    return "опубликован" in status


def is_our_lot(lot: dict) -> bool:
    text = (
        (lot.get("name_ru") or "") + " " +
        (lot.get("description_ru") or "")
    ).lower()

    return any(word in text for word in KEYWORDS)


def filter_lots(lots: list[dict]) -> list[dict]:
    return [
        lot for lot in lots
        if is_open_lot(lot) and is_our_lot(lot)
    ]
