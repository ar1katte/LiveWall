import os
import uuid
import telebot
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
import database

load_dotenv()
database.init_db()

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'token')
BOARD_URL  = os.environ.get('BOARD_URL', 'http://127.0.0.1:5000')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

anon_users = set()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/messages')
def get_messages():
    return jsonify(database.get_latest_messages(50))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    return 'Forbidden', 403

from telebot import types

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Написать вопрос"))
    markup.row(types.KeyboardButton("Анонимный режим"), types.KeyboardButton("Ссылка на доску"))
    markup.row(types.KeyboardButton("Помощь"))
    status = "анон включен" if message.from_user.id in anon_users else "от своего имени"
    bot.reply_to(
        message,
        f"Привет, {message.from_user.first_name}.\n\n"
        "Пиши вопросы сюда, они будут на доске.\n\n"
        f"Статус: {status}.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Анонимный режим")
def toggle_anon(message):
    uid = message.from_user.id
    if uid in anon_users:
        anon_users.discard(uid)
        bot.send_message(message.chat.id, "Анон выключен.")
    else:
        anon_users.add(uid)
        bot.send_message(message.chat.id, "Анон включен.")

@bot.message_handler(func=lambda m: m.text == "Ссылка на доску")
def send_link(message):
    bot.send_message(message.chat.id, f"Доска тут: {BOARD_URL}")

@bot.message_handler(func=lambda m: m.text == "Помощь")
def send_help(message):
    bot.send_message(message.chat.id, "Просто пиши текст, он появится на доске. Есть кнопка анонимности.")

@bot.message_handler(func=lambda m: m.text == "Написать вопрос")
def prompt_question(message):
    bot.send_message(message.chat.id, "Жду вопрос.")

def get_user_photo(user_id):
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            file_info = bot.get_file(file_id)
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    except:
        pass
    return None

@bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'audio', 'voice'])
def process_message(message):
    uid = message.from_user.id
    if message.text and message.text.startswith(("Аноним", "Ссылка", "Помощь", "Написать")):
        return

    if uid in anon_users:
        username = "Аноним"
        photo_url = None
    else:
        username = message.from_user.first_name
        if message.from_user.last_name:
            username += f" {message.from_user.last_name}"
        photo_url = get_user_photo(uid)

    text = (message.text or message.caption or "")[:500]
    media_url = None
    media_type = None
    file_info_obj = None

    if message.photo: file_info_obj, media_type = message.photo[-1], 'photo'
    elif message.document: file_info_obj, media_type = message.document, 'document'
    elif message.video: file_info_obj, media_type = message.video, 'video'
    elif message.audio: file_info_obj, media_type = message.audio, 'audio'
    elif message.voice: file_info_obj, media_type = message.voice, 'audio'

    if file_info_obj:
        try:
            fi = bot.get_file(file_info_obj.file_id)
            data = bot.download_file(fi.file_path)
            ext = os.path.splitext(fi.file_path)[1]
            if not ext:
                ext = {'photo': '.jpg', 'video': '.mp4', 'audio': '.ogg'}.get(media_type, '.bin')
            filename = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(UPLOADS_DIR, filename)
            with open(file_path, 'wb') as f: f.write(data)
            media_url = f"/static/uploads/{filename}"
        except: pass

    database.add_message(uid, username, photo_url, text, media_url, media_type)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Открыть доску", url=BOARD_URL))
    bot.reply_to(message, "Принято.", reply_markup=markup)

if __name__ == '__main__':
    import threading
    bot.remove_webhook()
    def run_bot():
        bot.infinity_polling()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
