# data/students_manager.py

from PyQt6.QtCore import QDate
from .db import get_connection, init_db

# Copyright 2025 Your Name
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

# Инициализация БД (создание таблиц и миграций)
init_db()


def load_students():
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем всех студентов
    cursor.execute("SELECT * FROM students")
    student_rows = cursor.fetchall()
    students = []

    for row in student_rows:
        student = {
            "id":          row["id"],
            "last_name":   row["last_name"],
            "first_name":  row["first_name"],
            "middle_name": row["middle_name"],
            "class":       row["class"],
            "parallel":    row["parallel"],
            "books":       []
        }

        # Извлекаем и библиотечные, и пользовательские книги
        cursor.execute(
            """
            SELECT
              sb.book_id,
              sb.due_date,
              sb.return_date,
              sb.returned,
              sb.custom_title,
              sb.custom_author,
              b.title  AS lib_title,
              b.author AS lib_author
            FROM student_books sb
            LEFT JOIN books b ON sb.book_id = b.id
            WHERE sb.student_id = ?
            """,
            (row["id"],)
        )

        for rb in cursor.fetchall():
            # Преобразуем даты в формат dd.MM.yyyy
            due_iso = rb["due_date"] or ""
            return_iso = rb["return_date"] or ""
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
            returned_flag = bool(rb["returned"])

            # Определяем источник title/author
            if rb["book_id"] is not None:
                title = rb["lib_title"] or ""
                author = rb["lib_author"] or ""
            else:
                title = rb["custom_title"] or ""
                author = rb["custom_author"] or ""

            # Формируем строку для отображения
            if author:
                display_str = f"{title} - {author}"
            else:
                display_str = title

            # Добавляем запись в student["books"]
            student["books"].append({
                "book":        display_str,
                "issue_date":  issue_date,
                "return_date": return_date,
                "returned":    returned_flag
            })

        students.append(student)

    conn.close()
    return students


def save_students(students):
    conn = get_connection()
    cursor = conn.cursor()

    # Существующие студенты
    cursor.execute("SELECT id FROM students")
    existing_ids = {r["id"] for r in cursor.fetchall()}
    new_ids = set()

    for student in students:
        # Добавление/обновление студента
        if student.get("id") in existing_ids:
            sid = student["id"]
            cursor.execute(
                """
                UPDATE students
                SET last_name = ?, first_name = ?, middle_name = ?, class = ?, parallel = ?
                WHERE id = ?
                """,
                (
                    student["last_name"],
                    student["first_name"],
                    student["middle_name"],
                    student["class"],
                    student["parallel"],
                    sid
                )
            )
        else:
            cursor.execute(
                """
                INSERT INTO students (last_name, first_name, middle_name, class, parallel)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    student["last_name"],
                    student["first_name"],
                    student["middle_name"],
                    student["class"],
                    student["parallel"]
                )
            )
            sid = cursor.lastrowid
            student["id"] = sid

        new_ids.add(sid)

        # Очищаем старые записи выдачи
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))

        # Сохраняем новые выдачи
        for be in student.get("books", []):
            disp = be.get("book", "").strip()
            if not disp:
                continue

            # Даты обратно в ISO
            qd = QDate.fromString(be.get("issue_date", ""), "dd.MM.yyyy")
            issue_iso = qd.toString("yyyy-MM-dd") if qd.isValid() else None
            qr = QDate.fromString(be.get("return_date", ""), "dd.MM.yyyy")
            return_iso = qr.toString("yyyy-MM-dd") if qr.isValid() else None
            returned_flag = 1 if be.get("returned", False) else 0

            # Разбор display_str на title и author
            if " - " in disp:
                title, author = disp.split(" - ", 1)
            else:
                title, author = disp, ""
            title = title.strip()
            author = author.strip()

            # Проверяем наличие в books
            cursor.execute(
                "SELECT id FROM books WHERE title = ? AND author = ?",
                (title, author)
            )
            book_row = cursor.fetchone()
            if book_row:
                book_id = book_row["id"]
                custom_title = None
                custom_author = None
            else:
                book_id = None
                custom_title = title
                custom_author = author

            # Вставляем запись выдачи в student_books
            cursor.execute(
                """
                INSERT INTO student_books
                  (student_id, book_id, due_date, return_date, returned, custom_title, custom_author)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    book_id,
                    issue_iso or '',
                    return_iso or '',
                    returned_flag,
                    custom_title,
                    custom_author
                )
            )

    # Удаляем студентов, которых больше нет
    to_delete = existing_ids - new_ids
    for sid in to_delete:
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))
        cursor.execute("DELETE FROM students WHERE id = ?", (sid,))

    conn.commit()
    conn.close()
