# handlers/passport_handler.py

from telebot import TeleBot, types
from services.mindee_service import extract_passport_data
from services.openai_service import generate_bot_response
from utils.state_manager import get_state, set_state, clear_state
import config


def handle_passport_photo(bot: TeleBot, message):
    """
    Handles the user's passport photo upload.
    Extracts data using Mindee API and asks the user to confirm the extracted details.
    """

    print("[DEBUG] Passport Handler - Processing photo")
    user_id = message.from_user.id
    current_state = get_state(user_id)

    # Only respond if user is in the correct state
    if current_state != "awaiting_passport":
        print(f"[DEBUG] Passport Handler - Ignored photo. Expected state: 'awaiting_passport', got: '{current_state}'")
        return

    # Notify the user that we're processing the passport
    processing_prompt = "The user has uploaded a passport photo. Please confirm that you are now processing the document."
    bot.send_message(message.chat.id, generate_bot_response(processing_prompt))

    try:
        # Get the highest resolution image from the message
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Use Mindee API to extract data from the passport image
        extracted_data = extract_passport_data(downloaded_file, config.MINDEE_API_KEY)

        if not extracted_data:
            raise ValueError("Не вдалося витягти дані з паспорта")

        # Extract prediction data from the response
        prediction = (
            extracted_data.get("document", {})
            .get("inference", {})
            .get("prediction", {})
        )

        # Extract key information from the prediction
        surname = prediction.get("surname", {}).get("value", "-")
        given_names = prediction.get("given_names", [{}])[0].get("value", "-")
        birth_date = prediction.get("birth_date", {}).get("value", "-")

        # Initialize user data storage if needed
        bot.user_data = getattr(bot, "user_data", {})
        if user_id not in bot.user_data:
            bot.user_data[user_id] = {}

        # Save passport data to user context
        bot.user_data[user_id]["passport"] = {
            "surname": surname,
            "given_names": [given_names],
            "birth_date": birth_date
        }
        bot.user_data[user_id]["confirmed"] = False  # Default confirmation status

        # Generate summary prompt asking for confirmation
        summary_prompt = f"Summarize and ask the user to confirm their passport details: Name: {given_names}, Surname: {surname}, Date of Birth: {birth_date}"
        summary_message = generate_bot_response(summary_prompt)
        bot.send_message(message.chat.id, summary_message)

        # Provide inline buttons for confirmation
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Yes", callback_data="confirm_passport_yes"),
            types.InlineKeyboardButton("❌ No", callback_data="confirm_passport_no")
        )
        bot.send_message(message.chat.id, "Are the details correct?", reply_markup=markup)

        # Move to confirmation state
        set_state(user_id, "confirm_passport")

    except Exception as e:
        # Log and inform the user about any errors
        print(f"[Data Extraction] Error: {e}")
        error_prompt = "There was an issue reading the passport. Please upload a clearer image."
        bot.send_message(message.chat.id, generate_bot_response(error_prompt))


def register_passport_callback_handlers(bot: TeleBot):
    """
    Registers inline button handlers for confirming or rejecting passport data.
    """

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_passport_"))
    def handle_confirmation(call):
        user_id = call.from_user.id
        current_state = get_state(user_id)

        if current_state != "confirm_passport":
            bot.answer_callback_query(call.id, "Unknown request.")
            return

        if call.data == "confirm_passport_yes":
            # User confirmed the data
            bot.user_data[user_id]["confirmed"] = True

            # Inform them what to do next (upload vehicle document)
            response_prompt = "The passport data has been confirmed. Please send a clear photo of the front page of your vehicle registration certificate, where the license plate number is visible."
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=generate_bot_response(response_prompt),
                reply_markup=None
            )

            # Move to next step in the process
            set_state(user_id, "awaiting_vehicle_doc_license_plate")
            print(f"[DEBUG] Passport Handler - State set to 'awaiting_vehicle_doc' for user {user_id}")

        elif call.data == "confirm_passport_no":
            # Data rejected — reset and ask for re-upload
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

        bot.answer_callback_query(call.id)  # Dismiss loading spinner