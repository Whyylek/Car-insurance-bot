# bot.py

import telebot
from handlers import register_all_handlers
import config

# Initialize the bot with the token from the config file
bot = telebot.TeleBot(config.BOT_TOKEN)

# Dictionary to store user data during interactions
bot.user_data = {}

# Register all handlers (commands, messages, callbacks, etc.)
register_all_handlers(bot)

# Start the bot if this script is run directly
if __name__ == "__main__":
    print("Бот запущено...")  # Bot started
    bot.polling(none_stop=True)  # Start polling for updates