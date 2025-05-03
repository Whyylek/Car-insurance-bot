
from telebot import TeleBot, types
from services.mindee_service import extract_passport_data
from services.openai_service import generate_bot_response
from utils.state_manager import get_state, set_state, clear_state
import config
#from typing import Optional, Dict
def handle_passport_photo(bot: TeleBot, message):
    print("[DEBUG] Passport Handler - Processing photo")
    user_id = message.from_user.id
    current_state = get_state(user_id)

    if current_state != "awaiting_passport":
        print(f"[DEBUG] Passport Handler - Ignored photo. Expected state: 'awaiting_passport', got: '{current_state}'")
        return  # Не наш стан

    # Повідомлення через OpenAI
    processing_prompt = "The user has uploaded a passport photo. Please confirm that you are now processing the document."
    bot.send_message(message.chat.id, generate_bot_response(processing_prompt))

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        extracted_data = extract_passport_data(downloaded_file, config.MINDEE_API_KEY)

        if not extracted_data:
            raise ValueError("Не вдалося витягти дані з паспорта")

        prediction = (
            extracted_data.get("document", {})
            .get("inference", {})
            .get("prediction", {})
        )

        surname = prediction.get("surname", {}).get("value", "-")
        given_names = prediction.get("given_names", [{}])[0].get("value", "-")
        birth_date = prediction.get("birth_date", {}).get("value", "-")

        # Зберігаємо дані
        bot.user_data = getattr(bot, "user_data", {})
        if user_id not in bot.user_data:
            bot.user_data[user_id] = {}
        bot.user_data[user_id]["passport"] = {
            "surname": surname,
            "given_names": [given_names],
            "birth_date": birth_date
        }
        bot.user_data[user_id]["confirmed"] = False

        # Підтвердження через OpenAI
        summary_prompt = f"Summarize and ask the user to confirm their passport details: Name: {given_names}, Surname: {surname}, Date of Birth: {birth_date}"
        summary_message = generate_bot_response(summary_prompt)
        bot.send_message(message.chat.id, summary_message)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Yes", callback_data="confirm_passport_yes"),
            types.InlineKeyboardButton("❌ No", callback_data="confirm_passport_no")
        )
        bot.send_message(message.chat.id, "Are the details correct?", reply_markup=markup)

        set_state(user_id, "confirm_passport")

    except Exception as e:
        print(f"[Data Extraction] Error: {e}")
        error_prompt = "There was an issue reading the passport. Please upload a clearer image."
        bot.send_message(message.chat.id, generate_bot_response(error_prompt))

def register_passport_callback_handlers(bot: TeleBot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_passport_"))
    def handle_confirmation(call):
        user_id = call.from_user.id
        current_state = get_state(user_id)

        if current_state != "confirm_passport":
            bot.answer_callback_query(call.id, "Unknown request.")
            return

        if call.data == "confirm_passport_yes":
            # Підтверджено — зберігаємо позитивний стан
            bot.user_data[user_id]["confirmed"] = True

            # Підтвердження через OpenAI
            response_prompt = "The passport data has been confirmed. Please send a photo of your vehicle documents next."
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_response(response_prompt),
                reply_markup=None
            )

            set_state(user_id, "awaiting_vehicle_doc")
            print(f"[DEBUG] Passport Handler - State set to 'awaiting_vehicle_doc' for user {user_id}")

        elif call.data == "confirm_passport_no":
            # Дані не вірні → скидаємо і просимо ще раз
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_response("Please re-upload your passport photo."),
                reply_markup=None
            )

            clear_state(user_id)
            set_state(user_id, "awaiting_passport")
            print(f"[DEBUG] Passport Handler - State reset to 'awaiting_passport' for user {user_id}")

        bot.answer_callback_query(call.id)  # Прибирає годинник завантаження