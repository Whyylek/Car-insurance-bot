# handlers/vehicle_handler.py

import logging
from telebot import TeleBot, types
from services.mindee_service import extract_vehicle_data
from services.openai_service import generate_bot_response
from utils.state_manager import get_state, set_state, clear_state
import config

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def handle_vehicle_photo(bot: TeleBot, message):
    logger.debug("[Vehicle Handler] Processing vehicle document photo")
    user_id = message.from_user.id
    current_state = get_state(user_id)

    logger.info(f"[Vehicle Handler] User {user_id} in state '{current_state}'")

    if current_state != "awaiting_vehicle_doc":
        logger.warning(f"[Vehicle Handler] Ignored photo. Expected state: 'awaiting_vehicle_doc', got: '{current_state}'")
        return  # не наш стан

    try:
        # Повідомлення через OpenAI
        processing_prompt = "The user has uploaded a vehicle document (PTS). Please confirm that you are now processing it."
        bot.send_message(message.chat.id, generate_bot_response(processing_prompt))

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        prediction = extract_vehicle_data(downloaded_file, config.MINDEE_API_KEY)
        logger.debug(f"[Vehicle Handler] Extracted prediction: {prediction}")

        if not prediction:
            raise ValueError("Не вдалося витягти дані з ПТС")

        vin = prediction.get("vin", "-")
        license_plate = prediction.get("license_plate", "-")

        bot.user_data = getattr(bot, "user_data", {})
        if user_id not in bot.user_data:
            bot.user_data[user_id] = {}

        bot.user_data[user_id]["vehicle"] = {
            "vin": vin,
            "license_plate": license_plate
        }
        bot.user_data[user_id]["confirmed"] = False

        # Запит на підтвердження через OpenAI
        summary_prompt = f"Summarize and ask the user to confirm their vehicle details: VIN: {vin}, License Plate: {license_plate}"
        summary_message = generate_bot_response(summary_prompt)
        bot.send_message(message.chat.id, summary_message)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Yes", callback_data="confirm_vehicle_yes"),
            types.InlineKeyboardButton("❌ No", callback_data="confirm_vehicle_no")
        )
        bot.send_message(message.chat.id, "Are the details correct?", reply_markup=markup)

        set_state(user_id, "confirm_vehicle")

    except Exception as e:
        logger.error(f"[Vehicle Extraction] Error: {e}")
        error_prompt = "There was an issue reading your vehicle document. Please upload a clearer image."
        bot.send_message(message.chat.id, generate_bot_response(error_prompt))


def register_vehicle_callback_handlers(bot: TeleBot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_vehicle_"))
    def handle_vehicle_confirmation(call):
        user_id = call.from_user.id
        current_state = get_state(user_id)

        logger.debug(f"[Vehicle Handler] Callback received. State: '{current_state}'")

        if current_state != "confirm_vehicle":
            bot.answer_callback_query(call.id, "Unknown request.")
            return

        if call.data == "confirm_vehicle_yes":
            bot.user_data[user_id]["confirmed"] = True
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_response("The vehicle data has been confirmed. Proceeding to price confirmation.")
            )

            set_state(user_id, "price_confirmation")
            logger.info(f"[Vehicle Handler] State set to 'price_confirmation' for user {user_id}")

            # Імпортуємо тут, щоб уникнути циклічних імпортів
            from handlers.price_handler import ask_price_confirmation
            ask_price_confirmation(bot, call.message)

        elif call.data == "confirm_vehicle_no":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_response("Please re-upload your vehicle document.")
            )

            clear_state(user_id)
            set_state(user_id, "awaiting_vehicle_doc")
            logger.info(f"[Vehicle Handler] State reset to 'awaiting_vehicle_doc' for user {user_id}")

        bot.answer_callback_query(call.id)  # Прибирає годинник завантаження