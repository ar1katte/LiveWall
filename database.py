import os
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'messages.db')

def init_db():
    # создаем таблицу если нет
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
                media_url TEXT,
                media_type TEXT
            )
        ''')
        # миграции
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN media_url TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN media_type TEXT')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()

def add_message(user_id, user_name, photo_url, text, media_url=None, media_type=None):
    # сохраняем месседж
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, user_name, photo_url, text, timestamp, media_url, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, photo_url, text, timestamp, media_url, media_type))
        conn.commit()

def get_latest_messages(limit=50):
    # достаем последние 50
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, user_name, photo_url, text, timestamp, media_url, media_type 
            FROM messages 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
