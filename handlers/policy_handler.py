# handlers/policy_handler.py

from services.openai_service import generate_insurance_policy
from utils.pdf_generator import generate_pdf
from telebot import TeleBot, types
import os

from utils.state_manager import get_state, set_state
from services.openai_service import generate_bot_response

# Configure logging


def send_insurance_policy_handler(message: types.Message, bot: TeleBot):
    """
    Handles the generation and delivery of the insurance policy document.
    - Uses user data to generate a policy using OpenAI
    - Converts the result into a PDF
    - Sends the PDF to the user
    - Deletes the temporary file afterward
    """

    chat_id = message.chat.id
    print(f"[Policy] Generating policy for user {chat_id}")

    try:
        # Check if user data exists
        user_data = bot.user_data.get(chat_id)

        if not user_data:
            print(f"[Policy] No user data found for chat_id={chat_id}")
            bot.send_message(chat_id, "⚠️ Error: No data to generate the policy.")
            return

        print(f"[Policy] User data: {user_data}")

        # Notify user that the policy is being generated
        bot.send_message(chat_id, "📄 Generating your insurance policy...")

        # Generate policy text using OpenAI
        policy_text = generate_insurance_policy(user_data)

        # Define path for the PDF file
        pdf_path = f"policy_{chat_id}.pdf"

        # Create the PDF document
        generate_pdf(policy_text, pdf_path)
        print(f"[Policy] PDF generated at {pdf_path}")

        # Send the PDF document to the user
        with open(pdf_path, "rb") as pdf_file:
            bot.send_document(chat_id, pdf_file)
            print(f"[Policy] Policy sent to user {chat_id}")

        # Inform the user about the generated policy
        summary_prompt = "Inform the user that the insurance policy is ready and they can review it in the attached file."
        summary_message = generate_bot_response(summary_prompt)
        bot.send_message(message.chat.id, summary_message)

        # Delete the temporary PDF file after sending
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"[Policy] Deleted temporary file {pdf_path}")

        # Update user state to reflect completion
        set_state(chat_id, "policy_sent")

    except Exception as e:
        # Log and inform the user about any errors
        print(f"[Policy] Error generating policy for user {chat_id}: {e}")
        bot.send_message(chat_id, "❌ An error occurred while generating the policy.")


def register_policy_handler(bot: TeleBot):
    """
    Registers the handler for sending the insurance policy.
    Triggers only when the user is in the 'confirm_purchase' state.
    """

    @bot.message_handler(func=lambda message: get_state(message.chat.id) == "confirm_purchase")
    def handler_wrapper(message: types.Message):
        send_insurance_policy_handler(message, bot)