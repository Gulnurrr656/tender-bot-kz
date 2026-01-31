# app/api/client.py

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

SEARCH_URL = "https://goszakup.gov.kz/ru/search/lots"

# Базовый keyword (на всякий)
KEYWORD = "куртка"

# ✅ Расширенный список для поиска
SEARCH_KEYWORDS = [
    # одежда / одноразка
    "халат",
    "маска",
    "перчатки",
    "бахилы",
    "комбинезон",
    "форма",

    # закупки / поставки
    "поставка",
    "приобретение",

    # работы / услуги
    "ремонт",
    "монтаж",
    "обслуживание",

    # IT
    "сайт",
    "портал",
    "информационная система",
    "программное обеспечение",
    "техническая поддержка",
]


async def get_lots_by_keyword(keyword: str = KEYWORD) -> list[dict]:
    """
    ✅ ТВОЯ СТАРАЯ get_lots, просто переименована.
    Логика НЕ ломается.
    """
    lots: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1️⃣ Открываем страницу
        await page.goto(SEARCH_URL, timeout=60000)

        # 2️⃣ Ждём поле поиска
        await page.wait_for_selector(
            'input[placeholder*="Наименование"]',
            state="attached",
            timeout=60000
        )

        # 3️⃣ Вводим ключевое слово
        await page.fill(
            'input[placeholder*="Наименование"]',
            keyword
        )

        # 4️⃣ Нажимаем кнопку "Найти"
        await page.click('button:has-text("Найти")')

        # ✅ 5️⃣ Ждём окончания XHR / JS
        await page.wait_for_load_state("networkidle")

        # ✅ 6️⃣ Ждём строки (DOM attached, не visible)
        await page.wait_for_selector(
            "table tbody tr",
            state="attached",
            timeout=60000
        )

        # 7️⃣ Забираем HTML
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")

    print(f"🔎 '{keyword}': HTML строк найдено: {len(rows)}")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        link_tag = cols[1].find("a")
        link = link_tag["href"] if link_tag else ""

        lots.append({
            "lot_number": cols[0].get_text(strip=True),
            "name_ru": cols[1].get_text(strip=True),
            "amount": cols[4].get_text(strip=True),
            "status_ru": cols[6].get_text(strip=True),
            "url": f"https://goszakup.gov.kz{link}" if link else "",
        })

    return lots


async def get_lots() -> list[dict]:
    """
    ✅ Новая безопасная обёртка:
    - прогоняет несколько ключей
    - объединяет результаты
    - убирает дубли по url
    """
    all_lots: list[dict] = []
    seen: set[str] = set()

    for kw in SEARCH_KEYWORDS:
        try:
            lots = await get_lots_by_keyword(kw)
        except Exception as e:
            print(f"⚠️ Ошибка поиска по '{kw}': {e}")
            continue

        for lot in lots:
            key = lot.get("url") or f'{lot.get("lot_number")}|{lot.get("name_ru")}'
            if key in seen:
                continue
            seen.add(key)
            all_lots.append(lot)

    print(f"📦 Всего лотов после объединения: {len(all_lots)}")
    return all_lots


# 🧪 локальный тест
if __name__ == "__main__":
    import asyncio

    result = asyncio.run(get_lots())
    print("Лотов получено:", len(result))
    for r in result[:5]:
        print(r)
