from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        locale="ru-RU",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    # 🔥 СРАЗУ идём на поиск лотов
    page.goto(
        "https://v3bl.goszakup.gov.kz/ru/search/lots",
        timeout=60000,
        wait_until="domcontentloaded"
    )

    print("URL после загрузки:", page.url)

    # если редиректнуло на логин — кликаем вручную
    if "/user/login" in page.url:
        print("⚠️ Редирект на логин, кликаем 'Поиск лотов'")
        page.click("text=Поиск лотов")
        page.wait_for_timeout(3000)

    # ждём именно таблицу
    page.wait_for_selector("table", timeout=60000)
    page.wait_for_selector("table tbody tr", timeout=60000)

    rows = page.query_selector_all("table tbody tr")
    print("✅ Найдено строк:", len(rows))

    if rows:
        print("⬇️ ПЕРВАЯ СТРОКА:")
        print(rows[0].inner_text())

    input("ENTER — закрыть браузер")
    browser.close()
