import os
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'messages.db')

def init_db():
    # создаем таблицу
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                photo_url TEXT,
                text TEXT,
                timestamp TEXT,
                media_type TEXT,
                media_blob BLOB
            )
        ''')
        # миграция на всякий
        try: cursor.execute('ALTER TABLE messages ADD COLUMN media_blob BLOB')
        except: pass
        conn.commit()

def add_message(user_id, user_name, photo_url, text, media_type=None, media_blob=None):
    # сохраняем всё в базу
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, user_name, photo_url, text, timestamp, media_type, media_blob)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, photo_url, text, timestamp, media_type, media_blob))
        conn.commit()

def get_latest_messages(limit=50):
    # возвращаем всё кроме тяжелого блоба
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, user_name, photo_url, text, timestamp, media_type
            FROM messages 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_media(msg_id):
    # достаем блоб для выдачи файла
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT media_blob, media_type FROM messages WHERE id=?', (msg_id,))
        return cursor.fetchone()
