import os
import sqlite3
import datetime

# Динамическое определение пути к базе данных
if os.path.exists('/home/arikatte'):
    DB_FILE = '/home/arikatte/project/messages.db'
else:
    # Локальный путь для ТВОЕГО компьютера
    DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.db')

def get_connection():
    """Создает подключение и гарантирует наличие таблицы."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Принудительно проверяем таблицу при каждом обращении
    conn.execute('''
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
    conn.commit()
    return conn

def init_db():
    """Начальная инициализация."""
    with get_connection() as conn:
        pass
    print(f"База данных готова: {DB_FILE}")

def add_message(user_id, user_name, photo_url, text, media_type=None, media_blob=None):
    """Сохранение сообщения в базу."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute('''
            INSERT INTO messages (user_id, user_name, photo_url, text, timestamp, media_type, media_blob)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, photo_url, text, ts, media_type, media_blob))

def get_latest_messages(limit=50):
    """Получение сообщений (без тяжелых файлов) для фронтенда."""
    with get_connection() as conn:
        cursor = conn.execute('''
            SELECT id, user_id, user_name, photo_url, text, timestamp, media_type
            FROM messages ORDER BY id DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_media(msg_id):
    """Получение бинарных данных (фото/видео) по ID сообщения."""
    with get_connection() as conn:
        res = conn.execute('SELECT media_blob, media_type FROM messages WHERE id=?', (msg_id,)).fetchone()
        return res if res else (None, None)
