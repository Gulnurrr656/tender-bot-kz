# app/api/client.py

from __future__ import annotations

import asyncio
from typing import List, Dict, Set

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

SEARCH_URL = "https://goszakup.gov.kz/ru/search/lots"

KEYWORD = "куртка"

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

# ⛔ ЖЁСТКОЕ ограничение: один Chromium за раз
_BROWSER_SEMAPHORE = asyncio.Semaphore(1)


def _parse_lots(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")

    lots: List[Dict] = []
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


async def get_lots() -> List[Dict]:
    """
    СТАБИЛЬНЫЙ клиент:
    - один Chromium
    - один context
    - один page
    - последовательный прогон keywords
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

            all_lots: List[Dict] = []
            seen: Set[str] = set()

            try:
                for kw in SEARCH_KEYWORDS:
                    print(f"🔎 Поиск keyword='{kw}'")

                    try:
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

                        # ждём именно строки
                        await page.wait_for_selector(
                            "table tbody tr",
                            timeout=60000,
                        )

                        html = await page.content()
                        lots = _parse_lots(html)

                        print(f"   → найдено строк: {len(lots)}")

                        for lot in lots:
                            url = lot.get("url")
                            if not url or url in seen:
                                continue
                            seen.add(url)
                            all_lots.append(lot)

                        # 🔴 обязательная пауза
                        await asyncio.sleep(1.2)

                    except PWTimeoutError as e:
                        print(f"⏱️ Timeout keyword='{kw}': {e}")
                    except Exception as e:
                        print(f"❌ Ошибка keyword='{kw}': {repr(e)}")

            finally:
                await page.close()
                await context.close()
                await browser.close()
                print("🧹 Playwright: браузер закрыт")

            print(f"📦 Всего уникальных лотов: {len(all_lots)}")
            return all_lots


# 🧪 локальный тест
if __name__ == "__main__":
    import asyncio
    res = asyncio.run(get_lots())
    print("Лотов:", len(res))
    for r in res[:5]:
        print(r)