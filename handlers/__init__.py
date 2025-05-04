# handlers/__init__.py

from telebot import TeleBot, types
from .start_handler import register_start_handlers
from .passport_handler import handle_passport_photo, register_passport_callback_handlers
from .vehicle_handler import handle_vehicle_photo, register_vehicle_callback_handlers
from .price_handler import ask_price_confirmation, register_price_handler
from .policy_handler import register_policy_handler
from utils.state_manager import get_state


def register_all_handlers(bot: TeleBot):
    """
    Registers all the bot handlers in one place.
    This includes command handlers, callback handlers, and message/photo handlers.
    """

    # Register /start and welcome message handlers
    register_start_handlers(bot)

    # Register inline button handlers for passport data confirmation
    register_passport_callback_handlers(bot)

    # Register inline button handlers for vehicle data confirmation
    register_vehicle_callback_handlers(bot)

    # Register price confirmation handler
    register_price_handler(bot)

    # Register policy generation handler
    register_policy_handler(bot)

    # Unified photo handler for document uploads
    @bot.message_handler(content_types=['photo'])
    def combined_photo_handler(message):
        """
        Handles all incoming photos based on the user's current state.
        Routes the photo to the appropriate handler (passport or vehicle).
        """

        print("[DEBUG] [Photo Handler] Message received")
        user_id = message.from_user.id
        current_state = get_state(user_id)
        print(f"[DEBUG] [Photo Handler] User {user_id} in state '{current_state}'")

        if current_state == "awaiting_passport":
            print("[DEBUG] [Photo Handler] Passing to handle_passport_photo")
            handle_passport_photo(bot, message)
        elif current_state == "awaiting_vehicle_doc_license_plate":
            print("[DEBUG] [Photo Handler] Passing to handle_vehicle_photo (license plate)")
            handle_vehicle_photo(bot, message)
        elif current_state == "awaiting_vehicle_doc_vin":
            print("[DEBUG] [Photo Handler] Passing to handle_vehicle_photo (VIN)")
            handle_vehicle_photo(bot, message)
        else:
            print(f"[DEBUG] [Photo Handler] Ignored photo. State: '{current_state}'")
            bot.send_message(
                message.chat.id,
                "Please follow the order: first send your passport, then vehicle documents."
            )

    # Handle non-photo messages during document upload steps
    @bot.message_handler(func=lambda m: True, content_types=['text', 'document', 'audio', 'video'])
    def handle_non_photo_messages(message):
        """
        Handles any non-photo message when the bot is expecting a document/photo.
        Sends a helpful reminder to upload the correct type of image based on the current step.
        """

        print("[DEBUG] [Text Handler] Message received (any text/document/other)")
        user_id = message.from_user.id
        current_state = get_state(user_id)
        print(f"[DEBUG] [Text Handler] User {user_id} in state '{current_state}'")

        # Define valid states where only photo input is accepted
        valid_states = [
            "awaiting_passport",
            "awaiting_vehicle_doc_license_plate",
            "awaiting_vehicle_doc_vin"
        ]

        if current_state in valid_states:
            from services.openai_service import generate_bot_response

            prompt = ""

            if current_state == "awaiting_passport":
                prompt = "Please upload a clear photo of your passport."

            elif current_state == "awaiting_vehicle_doc_license_plate":
                prompt = "Please upload a clear photo of the vehicle's license plate."

            elif current_state == "awaiting_vehicle_doc_vin":
                prompt = "Please upload a clear photo with the vehicle's VIN code and make/model."

            bot.send_message(message.chat.id, generate_bot_response(prompt))

        else:
            print(f"[DEBUG] [Text Handler] Ignored message. Current state: '{current_state}'")