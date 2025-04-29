# data/db.py
import sqlite3
import os
from os.path import dirname, abspath, join

DB_PATH = join(dirname(abspath(__file__)), "library.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Создание основных таблиц
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        quantity INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        middle_name TEXT NOT NULL,
        class TEXT NOT NULL,
        parallel TEXT NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER,
        due_date TEXT NOT NULL,
        return_date TEXT,
        returned INTEGER DEFAULT 0,
        custom_title TEXT,
        custom_author TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )""")

    # 2) Миграции полей student_books
    cursor.execute("PRAGMA table_info(student_books)")
    cols = {row[1] for row in cursor.fetchall()}

    if 'return_date' not in cols:
        cursor.execute("ALTER TABLE student_books ADD COLUMN return_date TEXT")
    if 'returned' not in cols:
        cursor.execute("ALTER TABLE student_books ADD COLUMN returned INTEGER DEFAULT 0")
    if 'custom_title' not in cols:
        cursor.execute("ALTER TABLE student_books ADD COLUMN custom_title TEXT")
    if 'custom_author' not in cols:
        cursor.execute("ALTER TABLE student_books ADD COLUMN custom_author TEXT")

    conn.commit()
    conn.close()
