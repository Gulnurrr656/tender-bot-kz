import requests

def get_session():
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://v3bl.goszakup.gov.kz/",
    })

    # 🔐 ВСТАВЬ СЮДА СВОИ COOKIE ИЗ БРАУЗЕРА
    session.cookies.update({
        "SESSION": "ВСТАВЬ_ЗДЕСЬ",
        "JSESSIONID": "ВСТАВЬ_ЗДЕСЬ",
        "XSRF-TOKEN": "ВСТАВЬ_ЗДЕСЬ",
    })

    return session
