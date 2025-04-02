import os
import re
from os.path import dirname, abspath, join
from .db import get_connection, init_db

init_db()  # инициализируем БД

def load_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, quantity FROM books")
    rows = cursor.fetchall()
    books = []
    for row in rows:
        books.append({
            "id": row["id"],
            "Title": row["title"],
            "Author": row["author"],
            "quantity": row["quantity"]
        })
    conn.close()
    return books

def save_books(books):
    conn = get_connection()
    cursor = conn.cursor()
    # Для каждой книги выполняем UPDATE, если она уже существует, иначе INSERT
    for book in books:
        cursor.execute("SELECT id FROM books WHERE title = ? AND author = ?",
                       (book.get("Title", ""), book.get("Author", "")))
        row = cursor.fetchone()
        if row:
            # Обновляем запись
            cursor.execute("UPDATE books SET quantity = ? WHERE id = ?",
                           (book.get("quantity"), row["id"]))
            book["id"] = row["id"]
        else:
            cursor.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
                           (book.get("Title", ""), book.get("Author", ""), book.get("quantity")))
            book["id"] = cursor.lastrowid
    conn.commit()
    conn.close()
