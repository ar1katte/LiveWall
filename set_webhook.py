import os
import sys
import telebot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("Ошибка: нет BOT_TOKEN")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def set_webhook(url):
    webhook_url = f"{url.rstrip('/')}/webhook"
    print(f"Setting webhook: {webhook_url}")
    bot.remove_webhook()
    if bot.set_webhook(url=webhook_url):
        print("Webhook set.")
    else:
        print("Error setting webhook.")

def delete_webhook():
    print("Deleting webhook...")
    if bot.remove_webhook():
        print("Webhook deleted.")
    else:
        print("Error deleting webhook.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: python3 set_webhook.py [url|delete]")
        sys.exit(1)

    action = sys.argv[1]
    if action == 'delete':
        delete_webhook()
    else:
        set_webhook(action)
