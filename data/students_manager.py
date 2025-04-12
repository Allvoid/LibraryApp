# data/students_manager.py
import os
import json
from os.path import dirname, abspath, join
from PyQt6.QtCore import QDate
from .db import get_connection, init_db

init_db()  # инициализируем БД

def load_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    student_rows = cursor.fetchall()
    students = []
    for row in student_rows:
        student = {
            "id": row["id"],
            "last_name": row["last_name"],
            "first_name": row["first_name"],
            "middle_name": row["middle_name"],
            "class": row["class"],
            "parallel": row["parallel"],
            "books": []
        }
        cursor.execute("""
            SELECT sb.due_date, b.title, b.author
            FROM student_books sb
            JOIN books b ON sb.book_id = b.id
            WHERE sb.student_id = ?
        """, (row["id"],))
        book_rows = cursor.fetchall()
        for brow in book_rows:
            iso_date = brow["due_date"]
            if iso_date:
                qdate = QDate.fromString(iso_date, "yyyy-MM-dd")
                due_date = qdate.toString("dd.MM.yyyy") if qdate.isValid() else ""
            else:
                due_date = ""
            display_str = f'{brow["title"]} - {brow["author"]}'
            student["books"].append({"book": display_str, "due_date": due_date})
        students.append(student)
    conn.close()
    return students

def save_students(students):
    conn = get_connection()
    cursor = conn.cursor()
    # Получаем существующие ID учеников из БД
    cursor.execute("SELECT id FROM students")
    existing_ids = set(row["id"] for row in cursor.fetchall())

    new_ids = set()
    for student in students:
        if "id" in student and student["id"] in existing_ids:
            cursor.execute("""
                UPDATE students
                SET last_name = ?, first_name = ?, middle_name = ?, class = ?, parallel = ?
                WHERE id = ?
            """, (student["last_name"], student["first_name"], student["middle_name"],
                  student["class"], student["parallel"], student["id"]))
            new_ids.add(student["id"])
        else:
            cursor.execute("""
                INSERT INTO students (last_name, first_name, middle_name, class, parallel)
                VALUES (?, ?, ?, ?, ?)
            """, (student["last_name"], student["first_name"], student["middle_name"],
                  student["class"], student["parallel"]))
            student["id"] = cursor.lastrowid
            new_ids.add(student["id"])
        # Обновляем таблицу student_books для данного ученика:
        # Сначала удаляем старые записи, затем вставляем новые
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (student["id"],))
        for book_entry in student.get("books", []):
            display_str = book_entry.get("book", "")
            due_date_str = book_entry.get("due_date", "")
            qdate = QDate.fromString(due_date_str, "dd.MM.yyyy")
            iso_date = qdate.toString("yyyy-MM-dd") if qdate.isValid() else ""
            cursor.execute("SELECT id FROM books WHERE title || ' - ' || author = ?", (display_str,))
            book_row = cursor.fetchone()
            if book_row:
                book_id = book_row["id"]
                cursor.execute("""
                    INSERT INTO student_books (student_id, book_id, due_date)
                    VALUES (?, ?, ?)
                """, (student["id"], book_id, iso_date))
            else:
                # Если книга не найдена – пропускаем
                pass
    # Удаляем студентов, которых нет в новом списке
    to_delete = existing_ids - new_ids
    for student_id in to_delete:
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
