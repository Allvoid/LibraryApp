# data/db.py
import sqlite3
import os
from os.path import dirname, abspath, join

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

# Располагаем базу данных в корневой папке проекта
BASE_DIR = dirname(dirname(abspath(__file__)))
db_path = join(BASE_DIR, "library.db")

def get_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Таблица для конфигурации (храним в виде JSON)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """
    )
    # Таблица для книг
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        quantity INTEGER
    )
    """
    )
    # Таблица для учеников
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        middle_name TEXT NOT NULL,
        class TEXT NOT NULL,
        parallel TEXT NOT NULL
    )
    """
    )
    # Таблица для связи учеников и книг (выдача и возврат)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
    """
    )
    # Миграция: добавляем колонку return_date, если её нет
    cursor.execute("PRAGMA table_info(student_books)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'return_date' not in cols:
        cursor.execute("ALTER TABLE student_books ADD COLUMN return_date TEXT")
    conn.commit()
    conn.close()
