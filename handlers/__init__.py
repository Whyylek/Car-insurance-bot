# handlers/__init__.py

from telebot import TeleBot, types
from .start_handler import register_start_handlers
from .passport_handler import handle_passport_photo, register_passport_callback_handlers
from .vehicle_handler import handle_vehicle_photo, register_vehicle_callback_handlers
from .price_handler import ask_price_confirmation, register_price_handler
from .policy_handler import register_policy_handler
from utils.state_manager import get_state


def register_all_handlers(bot: TeleBot):
    # Реєстрація основних команд (/start)
    register_start_handlers(bot)

    # Реєстрація callback handlers для підтвердження
    register_passport_callback_handlers(bot)
    register_vehicle_callback_handlers(bot)

    # Реєстрація інших хендлерів
    register_price_handler(bot)
    register_policy_handler(bot)

    # Обробка фото (паспорт / ПТС)
    @bot.message_handler(content_types=['photo'])
    def combined_photo_handler(message):
        print("[DEBUG] [Photo Handler] Message received")
        user_id = message.from_user.id
        current_state = get_state(user_id)

        print(f"[DEBUG] [Photo Handler] User {user_id} in state '{current_state}'")

        if current_state == "awaiting_passport":
            print("[DEBUG] [Photo Handler] Passing to handle_passport_photo")
            handle_passport_photo(bot, message)
        elif current_state in ["awaiting_vehicle_doc_license_plate", "awaiting_vehicle_doc_vin"]:
            handle_vehicle_photo(bot, message)
        else:
            print(f"[DEBUG] [Photo Handler] Ignored photo. State: '{current_state}'")
            bot.send_message(
                message.chat.id,
                "Please follow the order: first send your passport, then vehicle documents."
            )

    # Обробка текстових повідомлень у станах завантаження документів
    @bot.message_handler(func=lambda m: True, content_types=['text', 'document', 'audio', 'video'])
    def handle_non_photo_messages(message):
        print("[DEBUG] [Text Handler] Message received (any text/document/other)")
        user_id = message.from_user.id
        current_state = get_state(user_id)

        print(f"[DEBUG] [Text Handler] User {user_id} in state '{current_state}'")

        if current_state in ["awaiting_passport", "awaiting_vehicle_doc"]:
            from services.openai_service import generate_bot_response

            if current_state == "awaiting_passport":
                print("[DEBUG] [Text Handler] Requesting passport photo again...")
                prompt = "The user tried to send something that is not a photo while in the passport upload step. Ask them to send a valid passport image."
                bot.send_message(message.chat.id, generate_bot_response(prompt))

            elif current_state == "awaiting_vehicle_doc":
                print("[DEBUG] [Text Handler] Requesting vehicle document photo again...")
                prompt = "The user tried to send something that is not a photo while in the vehicle document upload step. Ask them to send a valid vehicle document image."
                bot.send_message(message.chat.id, generate_bot_response(prompt))

        else:
            print(f"[DEBUG] [Text Handler] Ignored message. Current state: '{current_state}'")