# handlers/start_handler.py

from telebot import TeleBot, types
from services.openai_service import generate_bot_response


def register_start_handlers(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_start = types.KeyboardButton("🚗 Start")
        markup.add(btn_start)

        # Запит до OpenAI
        welcome_prompt = "The user has started the bot. Welcome them and ask to send their passport photo to begin the insurance process."
        reply_text = generate_bot_response(welcome_prompt)

        bot.send_message(
            message.chat.id,
            reply_text,
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == "🚗 Start")
    def handle_start(message):
        # Запит до OpenAI
        instruction_prompt = "Ask the user to send a photo of their passport to proceed with the car insurance application."
        reply_text = generate_bot_response(instruction_prompt)

        bot.send_message(
            message.chat.id,
            reply_text
        )

        from utils.state_manager import set_state
        set_state(message.from_user.id, "awaiting_passport")