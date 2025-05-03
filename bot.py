# bot.py
import telebot
from handlers import register_all_handlers
import config

bot = telebot.TeleBot(config.BOT_TOKEN)

# Для зберігання даних користувача
bot.user_data = {}

# Реєстрація всіх хендлерів
register_all_handlers(bot)

if __name__ == "__main__":
    print("Бот запущено...")
    bot.polling(none_stop=True)