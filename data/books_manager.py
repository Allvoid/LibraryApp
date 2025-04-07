import os
import re
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

init_db()  # Инициализируем базу, если еще не создана

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
    # Получаем все записи из базы в виде словаря по ключу (title, author)
    cursor.execute("SELECT id, title, author FROM books")
    existing = {}
    for row in cursor.fetchall():
        key = (row["title"], row["author"])
        existing[key] = row["id"]

    current_ids = set()
    for book in books:
        key = (book.get("Title", ""), book.get("Author", ""))
        if key in existing:
            book_id = existing[key]
            current_ids.add(book_id)
            cursor.execute("UPDATE books SET quantity = ? WHERE id = ?",
                           (book.get("quantity"), book_id))
            book["id"] = book_id
        else:
            cursor.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
                           (book.get("Title", ""), book.get("Author", ""), book.get("quantity")))
            book_id = cursor.lastrowid
            book["id"] = book_id
            current_ids.add(book_id)

    # Удаляем записи, которых нет в текущем списке
    if current_ids:
        placeholders = ','.join(['?'] * len(current_ids))
        cursor.execute(f"DELETE FROM books WHERE id NOT IN ({placeholders})", tuple(current_ids))
    else:
        cursor.execute("DELETE FROM books")

    conn.commit()
    conn.close()
