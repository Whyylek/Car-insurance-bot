# handlers/policy_handler.py

from services.openai_service import generate_insurance_policy
from utils.pdf_generator import generate_pdf
from telebot import TeleBot, types
import os
import logging
from utils.state_manager import get_state, set_state
from services.openai_service import generate_bot_response

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_insurance_policy_handler(message: types.Message, bot: TeleBot):
    chat_id = message.chat.id
    logger.info(f"[Policy] Generating policy for user {chat_id}")

    try:
        # Перевіряємо, чи є дані користувача
        user_data = bot.user_data.get(chat_id)

        if not user_data:
            logger.error(f"[Policy] No user data found for chat_id={chat_id}")
            bot.send_message(chat_id, "⚠️ Error: No data to generate the policy.")
            return

        logger.debug(f"[Policy] User data: {user_data}")
        bot.send_message(chat_id, "📄 Generating your insurance policy...")

        # Генеруємо текст полісу через OpenAI
        policy_text = generate_insurance_policy(user_data)

        # Створюємо PDF-файл
        pdf_path = f"policy_{chat_id}.pdf"
        generate_pdf(policy_text, pdf_path)

        # Відправляємо PDF
        with open(pdf_path, "rb") as pdf_file:
            bot.send_document(chat_id, pdf_file)
            logger.info(f"[Policy] Policy sent to user {chat_id}")

        summary_prompt = f"Inform the user that insurance policy are ready and he can read it in file"
        summary_message = generate_bot_response(summary_prompt)
        bot.send_message(message.chat.id, summary_message)

        # Видаляємо файл після відправки
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.debug(f"[Policy] Deleted temporary file {pdf_path}")

        # Змінюємо стан
        set_state(chat_id, "policy_sent")

    except Exception as e:
        logger.exception(f"[Policy] Error generating policy for user {chat_id}: {e}")
        bot.send_message(chat_id, "❌ An error occurred while generating the policy.")


# Ця функція реєструє хендлер (використовується в __init__.py)
def register_policy_handler(bot: TeleBot):
    @bot.message_handler(func=lambda message: get_state(message.chat.id) == "confirm_purchase")
    def handler_wrapper(message: types.Message):
        send_insurance_policy_handler(message, bot)