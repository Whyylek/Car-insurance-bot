# handlers/price_handler.py

from telebot import TeleBot, types
from services.openai_service import generate_bot_response
from utils.state_manager import get_state, set_state
from handlers.policy_handler import send_insurance_policy_handler


def ask_price_confirmation(bot: TeleBot, message):
    """
    Показує користувачу фіксовану ціну через Inline-кнопки.
    """
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ Yes", callback_data="price_agree")
    btn_no = types.InlineKeyboardButton("❌ No", callback_data="price_disagree")
    markup.add(btn_yes, btn_no)

    # Генеруємо відповідь через OpenAI
    prompt = "Inform the user about the fixed insurance price of $100 and ask if they agree to proceed."
    confirmation_text = generate_bot_response(prompt)

    bot.send_message(
        message.chat.id,
        confirmation_text,
        reply_markup=markup
    )
    set_state(message.from_user.id, "price_confirmation")


def register_price_handler(bot: TeleBot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_price_callback(call):
        user_id = call.from_user.id
        current_state = get_state(user_id)

        if current_state != "price_confirmation":
            bot.answer_callback_query(call.id, "Unknown request.")
            return

        if call.data == "price_agree":
            bot.answer_callback_query(call.id)
            response = generate_bot_response("The user has agreed to the price. Generating the insurance policy now.")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response
            )

            # Встановлюємо стан для логування
            set_state(user_id, "policy_generation")

            # Виклик хендлера полісу (передаємо лише message)
            send_insurance_policy_handler(call.message,bot)  # 'bot' вже доступний через замикання

        elif call.data == "price_disagree":
            bot.answer_callback_query(call.id)
            response = generate_bot_response("Unfortunately, the price of $100 is fixed and cannot be changed. Would you like to proceed with the purchase?")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                reply_markup=None
            )

            # Повторне запитання про погодження
            ask_price_confirmation(bot, call.message)

        else:
            bot.answer_callback_query(call.id, "Unknown command.")