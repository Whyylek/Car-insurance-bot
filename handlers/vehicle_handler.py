# handlers/vehicle_handler.py

from telebot import TeleBot, types
from services.mindee_service import extract_vehicle_data
from services.openai_service import generate_bot_response
from utils.state_manager import get_state, set_state, clear_state
import config

def handle_vehicle_photo(bot: TeleBot, message):
    """
    Handles incoming vehicle document photos from users.
    Extracts vehicle data using Mindee API and updates user state accordingly.
    """

    print("[Vehicle Handler] Processing vehicle document photo")
    user_id = message.from_user.id
    current_state = get_state(user_id)
    print(f"[Vehicle Handler] User {user_id} in state '{current_state}'")

    # Check if the user is expected to upload a vehicle document
    if current_state not in ["awaiting_vehicle_doc_license_plate", "awaiting_vehicle_doc_vin"]:
        print(f"[Vehicle Handler] Ignored photo. Expected states: 'awaiting_vehicle_doc_license_plate' or 'awaiting_vehicle_doc_vin', got: '{current_state}'")
        return

    try:
        # Get the highest resolution photo
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Use Mindee to extract data from the image
        prediction = extract_vehicle_data(downloaded_file, config.MINDEE_API_KEY)
        print(f"[Vehicle Handler] Extracted prediction: {prediction}")

        if not prediction:
            raise ValueError("Не вдалося витягти дані з документа")

        # Initialize user data storage if needed
        bot.user_data = getattr(bot, "user_data", {})
        if user_id not in bot.user_data:
            bot.user_data[user_id] = {}

        # Handle based on current expected input
        if current_state == "awaiting_vehicle_doc_license_plate":
            license_plate = prediction.get("license_plate", "-")
            bot.user_data[user_id]["vehicle"] = {
                "license_plate": license_plate,
            }
            print(f"[Vehicle Handler] License plate saved: {license_plate}")
            set_state(user_id, "awaiting_vehicle_doc_vin")

            prompt = "Please upload a photo with the VIN code and make of the vehicle."
            bot.send_message(message.chat.id, generate_bot_response(prompt))

        elif current_state == "awaiting_vehicle_doc_vin":
            vin = prediction.get("vin", "-")
            make = prediction.get("make", "-")  # Make may be present in response
            model = prediction.get("model", "-")  # Model may also be available

            bot.user_data[user_id]["vehicle"].update({
                "vin": vin,
                "make": make,
                "model": model
            })
            print(f"[Vehicle Handler] VIN and make/model saved: {vin}, {make} {model}")

            # Ask user to confirm the extracted details
            set_state(user_id, "confirm_vehicle")
            summary_prompt = f"Summarize and ask the user to confirm their vehicle details: VIN: {vin}, Make: {make}, Model: {model}, License Plate: {bot.user_data[user_id]['vehicle']['license_plate']}"
            summary_message = generate_bot_response(summary_prompt)
            bot.send_message(message.chat.id, summary_message)

            # Provide confirmation buttons
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Yes", callback_data="confirm_vehicle_yes"),
                types.InlineKeyboardButton("❌ No", callback_data="confirm_vehicle_no")
            )
            bot.send_message(message.chat.id, "Are the details correct?", reply_markup=markup)

    except Exception as e:
        print(f"[Vehicle Extraction] Error: {e}")
        error_prompt = "There was an issue reading your vehicle document. Please upload a clearer image."
        bot.send_message(message.chat.id, generate_bot_response(error_prompt))


def register_vehicle_callback_handlers(bot: TeleBot):
    """
    Registers inline button callbacks for vehicle data confirmation.
    """

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_vehicle_"))
    def handle_vehicle_confirmation(call):
        user_id = call.from_user.id
        current_state = get_state(user_id)

        print(f"[Vehicle Handler] Callback received. State: '{current_state}'")

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
            print(f"[Vehicle Handler] State set to 'price_confirmation' for user {user_id}")

            # Import inside to avoid circular imports
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
            print(f"[Vehicle Handler] State reset to 'awaiting_vehicle_doc' for user {user_id}")

        bot.answer_callback_query(call.id)  # Dismiss loading spinner