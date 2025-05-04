# handlers/start_handler.py

from telebot import TeleBot, types
from services.openai_service import generate_bot_response


def register_start_handlers(bot: TeleBot):
    """
    Registers handlers for the /start command and the '🚗 Start' button.
    These handlers welcome the user and prompt them to upload a passport photo.
    """

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """
        Handles the '/start' command.
        Sends a friendly welcome message with a 'Start' button.
        """

        # Create a custom keyboard with a "Start" button
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_start = types.KeyboardButton("🚗 Start")
        markup.add(btn_start)

        # Generate a welcome message using OpenAI
        welcome_prompt = "The user has started the bot. Welcome them and ask to send their passport photo to begin the insurance process."
        reply_text = generate_bot_response(welcome_prompt)

        # Send the welcome message along with the keyboard
        bot.send_message(
            message.chat.id,
            reply_text,
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == "🚗 Start")
    def handle_start(message):
        """
        Handles when the user clicks the '🚗 Start' button.
        Prompts them to upload a photo of their passport.
        """

        # Ask the user to send their passport photo using AI-generated text
        instruction_prompt = "Ask the user to send a photo of their passport to proceed with the car insurance application."
        reply_text = generate_bot_response(instruction_prompt)

        bot.send_message(
            message.chat.id,
            reply_text
        )

        # Update the user's state to expect a passport photo
        from utils.state_manager import set_state
        set_state(message.from_user.id, "awaiting_passport")