import os
import telebot
from flask import Flask, request, render_template, jsonify, Response
import database

# Настройки
BOT_TOKEN = '8547486680:AAFmjAEvAwb4irHCi2P4VNiSSZgfH0ECyII'
BOARD_URL = 'https://arikatte.pythonanywhere.com'

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# Храним состояние анонимности в памяти (на сервере оно сбросится при Reload)
anon_users = set()

# Инициализируем БД при запуске
database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/messages')
def get_messages():
    try:
        msgs = database.get_latest_messages(50)
        return jsonify(msgs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/media/<int:msg_id>')
def get_media(msg_id):
    try:
        blob, mtype = database.get_media(msg_id)
        if not blob: return "No media", 404
        # Мапинг типов контента
        content_types = {'photo': 'image/jpeg', 'video': 'video/mp4'}
        return Response(blob, mimetype=content_types.get(mtype, 'application/octet-stream'))
    except:
        return "Error", 500

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    return 'Forbidden', 403

def get_user_photo(user_id):
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            file_info = bot.get_file(file_id)
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    except: pass
    return None

# --- ОБРАБОТЧИКИ БОТА ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Написать вопрос", "Анонимный режим")
    bot.send_message(message.chat.id, "Бот готов к работе.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Анонимный режим")
def toggle_anon(message):
    uid = message.from_user.id
    if uid in anon_users:
        anon_users.remove(uid)
        bot.send_message(message.chat.id, "Режим анонимности ВЫКЛЮЧЕН.")
    else:
        anon_users.add(uid)
        bot.send_message(message.chat.id, "Режим анонимности ВКЛЮЧЕН.")

@bot.message_handler(content_types=['text', 'photo', 'video'])
def process_message(message):
    # Игнорируем нажатия кнопок меню
    if message.text in ["Написать вопрос", "Анонимный режим"]:
        bot.send_message(message.chat.id, "Жду твой текст или файл...")
        return
    
    uid = message.from_user.id
    is_anon = uid in anon_users
    
    # Формируем данные
    username = "Аноним" if is_anon else message.from_user.first_name
    photo_url = None if is_anon else get_user_photo(uid)
    text = (message.text or message.caption or "")
    
    media_blob, media_type = None, None
    file_obj = None
    
    if message.photo:
        file_obj, media_type = message.photo[-1], 'photo'
    elif message.video:
        file_obj, media_type = message.video, 'video'

    if file_obj:
        try:
            fi = bot.get_file(file_obj.file_id)
            media_blob = bot.download_file(fi.file_path)
        except: pass

    try:
        database.add_message(uid, username, photo_url, text, media_type, media_blob)
        bot.send_message(message.chat.id, "Сообщение опубликовано на доске!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка сохранения в базу: {e}")

if __name__ == '__main__':
    # Если запуск локальный - удаляем вебхук и запускаем поллинг
    bot.remove_webhook()
    bot.infinity_polling()
