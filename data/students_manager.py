# data/students_manager.py
from PyQt6.QtCore import QDate
from .db import get_connection, init_db

# Copyright 2025 Your Name
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Initialize database and migration: add return_date column if missing
init_db()
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE student_books ADD COLUMN return_date TEXT")
except Exception:
    pass
conn.commit()
conn.close()

# Ensure DB tables exist
init_db()

def load_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, last_name, first_name, class, parallel FROM students")
    student_rows = cursor.fetchall()
    students = []
    for row in student_rows:
        student = {
            "id": row["id"],
            "last_name": row["last_name"],
            "first_name": row["first_name"],
            "class": row["class"],
            "parallel": row["parallel"],
            "books": []
        }
        cursor.execute(
            """
            SELECT sb.due_date, sb.return_date, b.title, b.author
            FROM student_books sb
            JOIN books b ON sb.book_id = b.id
            WHERE sb.student_id = ?
            """,
            (row["id"],)
        )
        book_rows = cursor.fetchall()
        for brow in book_rows:
            due_iso = brow["due_date"]
            return_iso = brow["return_date"]
            issue_date = ""
            return_date = ""
            if due_iso:
                qd = QDate.fromString(due_iso, "yyyy-MM-dd")
                if qd.isValid():
                    issue_date = qd.toString("dd.MM.yyyy")
            if return_iso:
                qr = QDate.fromString(return_iso, "yyyy-MM-dd")
                if qr.isValid():
                    return_date = qr.toString("dd.MM.yyyy")
            display_str = f'{brow["title"]} - {brow["author"]}'
            student["books"].append({
                "book": display_str,
                "issue_date": issue_date,
                "return_date": return_date
            })
        students.append(student)
    conn.close()
    return students


def save_students(students):
    conn = get_connection()
    cursor = conn.cursor()
    # Получаем существующих студентов
    cursor.execute("SELECT id FROM students")
    existing_ids = {row["id"] for row in cursor.fetchall()}
    new_ids = set()
    for student in students:
        # Вставка или обновление студента
        if "id" in student and student["id"] in existing_ids:
            cursor.execute(
                """
                UPDATE students
                SET last_name = ?, first_name = ?, class = ?, parallel = ?
                WHERE id = ?
                """,
                (
                    student["last_name"], student["first_name"],
                    student["class"], student["parallel"], student["id"]
                )
            )
            sid = student["id"]
        else:
            cursor.execute(
                """
                INSERT INTO students (last_name, first_name, middle_name, class, parallel)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    student["last_name"],
                    student["first_name"],
                    "",  # middle_name теперь всегда пустая строка
                    student["class"],
                    student["parallel"],
                )
            )
            sid = cursor.lastrowid
            student["id"] = sid
        new_ids.add(sid)

        # Сбрасываем старые записи выдачи
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))
        # Обрабатываем книги студента
        for book_entry in student.get("books", []):
            display_str = book_entry.get("book", "").strip()
            if not display_str:
                continue
            issue_str = book_entry.get("issue_date", "")
            return_str = book_entry.get("return_date", "")
            # Преобразуем даты в ISO
            qd = QDate.fromString(issue_str, "dd.MM.yyyy")
            issue_iso = qd.toString("yyyy-MM-dd") if qd.isValid() else None
            qr = QDate.fromString(return_str, "dd.MM.yyyy")
            return_iso = qr.toString("yyyy-MM-dd") if qr.isValid() else None

            # Ищем книгу в библиотеке
            cursor.execute(
                "SELECT id FROM books WHERE title || ' - ' || author = ?",
                (display_str,)
            )
            row_book = cursor.fetchone()
            if row_book:
                book_id = row_book["id"]
            else:
                # Создаём новую книгу, если не нашли
                if " - " in display_str:
                    title, author = display_str.split(" - ", 1)
                else:
                    title, author = display_str, ""
                cursor.execute(
                    "INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
                    (title.strip(), author.strip(), None)
                )
                book_id = cursor.lastrowid

            # Вставляем запись выдачи
            cursor.execute(
                """
                INSERT INTO student_books (student_id, book_id, due_date, return_date)
                VALUES (?, ?, ?, ?)
                """,
                (sid, book_id, issue_iso or '', return_iso or '')
            )
    # Удаляем студентов, которых нет в новом списке
    to_delete = existing_ids - new_ids
    for sid in to_delete:
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))
        cursor.execute("DELETE FROM students WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
