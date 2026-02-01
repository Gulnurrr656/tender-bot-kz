from __future__ import annotations

import asyncio
from typing import List, Dict, Set

from playwright.async_api import async_playwright

SEARCH_URL = "https://goszakup.gov.kz/ru/search/lots"

SEARCH_KEYWORDS = [
    "халат",
    "маска",
    "перчатки",
    "бахилы",
    "комбинезон",
    "форма",
    "поставка",
    "приобретение",
    "ремонт",
    "монтаж",
    "обслуживание",
    "сайт",
    "портал",
    "информационная система",
    "программное обеспечение",
    "техническая поддержка",
]

_BROWSER_SEMAPHORE = asyncio.Semaphore(1)


def _normalize_lot(item: Dict) -> Dict:
    """
    Приводим API-лот к формату,
    который уже ждёт твой бот.
    """
    return {
        "lot_number": str(item.get("lotNumber", "—")),
        "name_ru": item.get("nameRu") or item.get("nameKz") or "Без названия",
        "amount": item.get("amount", "—"),
        "status_ru": item.get("statusRu", "—"),
        "url": f"https://goszakup.gov.kz/ru/announce/index/{item.get('announceId')}",
    }


async def get_lots() -> List[Dict]:
    """
    СТАБИЛЬНЫЙ клиент через XHR API goszakup.gov.kz
    """
    async with _BROWSER_SEMAPHORE:
        print("🚀 Playwright: старт браузера")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            page = await context.new_page()

            collected: List[Dict] = []
            seen: Set[str] = set()

            async def on_response(response):
                if "/v3/lots/search" in response.url and response.request.method == "POST":
                    try:
                        data = await response.json()
                        items = data.get("items") or []
                        print(f"📥 API items: {len(items)}")

                        for item in items:
                            lot = _normalize_lot(item)
                            url = lot.get("url")
                            if url and url not in seen:
                                seen.add(url)
                                collected.append(lot)
                    except Exception as e:
                        print("❌ Ошибка чтения API:", e)

            page.on("response", on_response)

            try:
                for kw in SEARCH_KEYWORDS:
                    print(f"🔎 Поиск keyword='{kw}'")

                    await page.goto(
                        SEARCH_URL,
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )

                    await page.wait_for_selector(
                        'input[placeholder*="Наименование"]',
                        timeout=60000,
                    )

                    await page.fill(
                        'input[placeholder*="Наименование"]',
                        kw,
                    )

                    await page.click('button:has-text("Найти")')

                    # даём SPA время сходить в API
                    await asyncio.sleep(5)

            finally:
                await page.close()
                await context.close()
                await browser.close()
                print("🧹 Playwright: браузер закрыт")

            print(f"📦 Всего уникальных лотов: {len(collected)}")
            return collected


# локальный тест
if __name__ == "__main__":
    import asyncio

    res = asyncio.run(get_lots())
    print("Лотов:", len(res))
    for r in res[:5]:
        print(r)