# config.py
import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")