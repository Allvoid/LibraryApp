import sqlite3
import os
from os.path import dirname, abspath, join

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
    """)
    # Таблица для книг
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        quantity INTEGER
    )
    """)
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
    """)
    # Таблица для связи учеников и книг (выдача)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
    """)
    conn.commit()
    conn.close()
