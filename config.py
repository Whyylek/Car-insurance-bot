# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram bot token from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Mindee API key for document parsing services
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY")

# OpenAI API key for chatbot functionality
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")