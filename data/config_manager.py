import os
import json
from os.path import dirname, abspath, join
from .db import get_connection, init_db

init_db()  # инициализируем БД, если ещё не создана

def load_config():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'config'")
    row = cursor.fetchone()
    if row:
        try:
            config = json.loads(row["value"])
            conn.close()
            return config
        except Exception as e:
            print("Ошибка загрузки config:", e)
    conn.close()
    return {
        "classes": [str(i) for i in range(1, 12)],
        "parallels": ["А", "Б", "В", "Г", "Д", "Л", "М"]
    }

def save_config(config):
    conn = get_connection()
    cursor = conn.cursor()
    config_json = json.dumps(config, ensure_ascii=False, indent=4)
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("config", config_json))
    conn.commit()
    conn.close()
