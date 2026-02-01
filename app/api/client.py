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
    ⛔ ВРЕМЕННО НЕ ИСПОЛЬЗУЕТСЯ
    (оставляем как есть, НЕ ЛОМАЕМ)
    """
    lots: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(SEARCH_URL, timeout=60000)

        await page.wait_for_selector(
            'input[placeholder*="Наименование"]',
            state="attached",
            timeout=60000
        )

        await page.fill(
            'input[placeholder*="Наименование"]',
            keyword
        )

        await page.click('button:has-text("Найти")')

        await page.wait_for_load_state("networkidle")

        await page.wait_for_selector(
            "table tbody tr",
            state="attached",
            timeout=60000
        )

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


# ==========================================================
# ⛔ ВАЖНО: ВРЕМЕННО ГЛУШИМ Playwright
# ==========================================================

async def get_lots() -> list[dict]:
    """
    ⚠️ Playwright ВРЕМЕННО ОТКЛЮЧЁН
    Нужно ТОЛЬКО для проверки кнопок и логики бота
    """
    print("⚠️ Playwright временно отключён (debug mode)")
    return []


# 🧪 локальный тест
if __name__ == "__main__":
    import asyncio

    result = asyncio.run(get_lots())
    print("Лотов получено:", len(result))
