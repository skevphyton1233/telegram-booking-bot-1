import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_admin_id_raw = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN. Проверьте файл .env")

if not _admin_id_raw:
    raise ValueError("Не найден ADMIN_ID. Проверьте файл .env")

try:
    ADMIN_ID = int(_admin_id_raw)
except ValueError as exc:
    raise ValueError("ADMIN_ID в .env должен быть числом (Telegram ID)") from exc
