# data/config_manager.py
import os
import json
from os.path import dirname, abspath, join
from .db import get_connection, init_db

# Copyright 2025 Your Name
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
