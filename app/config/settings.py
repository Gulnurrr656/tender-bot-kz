import os
from dotenv import load_dotenv

# загружаем переменные окружения
load_dotenv()

# =====================
# API ГОСЗАКУПОК
# =====================
BASE_URL_API = os.getenv("BASE_URL_API")
API_TOKEN = os.getenv("API_TOKEN")

# =====================
# TELEGRAM
# =====================
TG_TOKEN = os.getenv("TG_TOKEN")
