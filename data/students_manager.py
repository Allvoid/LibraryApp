# data/students_manager.py
from PyQt6.QtCore import QDate
from .db import get_connection, init_db

# Copyright 2025 Your Name
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

# Initialize database and migration: add return_date, returned, returned_date columns if missing
init_db()
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE student_books ADD COLUMN return_date TEXT")
except Exception:
    pass
try:
    cursor.execute("ALTER TABLE student_books ADD COLUMN returned INTEGER DEFAULT 0")
except Exception:
    pass
try:
    cursor.execute("ALTER TABLE student_books ADD COLUMN returned_date TEXT")
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
            SELECT sb.due_date, sb.return_date AS planned_return, sb.returned, sb.returned_date, b.title, b.author
            FROM student_books sb
            JOIN books b ON sb.book_id = b.id
            WHERE sb.student_id = ?
            """,
            (row["id"],)
        )
        book_rows = cursor.fetchall()
        for brow in book_rows:
            # Original issue_date stored in due_date
            due_iso = brow["due_date"]
            # Planned return stored in return_date (renamed alias)
            planned_iso = brow["planned_return"]
            returned_flag = brow["returned"] if "returned" in brow.keys() else 0
            returned_iso = brow["returned_date"] if "returned_date" in brow.keys() else ''
            issue_date = ""
            return_date = ""
            if due_iso:
                qd = QDate.fromString(due_iso, "yyyy-MM-dd")
                if qd.isValid():
                    issue_date = qd.toString("dd.MM.yyyy")
            if planned_iso:
                qp = QDate.fromString(planned_iso, "yyyy-MM-dd")
                if qp.isValid():
                    return_date = qp.toString("dd.MM.yyyy")
            # returned_date
            actual_return = ""
            if returned_iso:
                qar = QDate.fromString(returned_iso, "yyyy-MM-dd")
                if qar.isValid():
                    actual_return = qar.toString("dd.MM.yyyy")
            display_str = f'{brow["title"]} - {brow["author"]}'
            student["books"].append({
                "book": display_str,
                "issue_date": issue_date,
                "return_date": return_date,
                "returned": bool(returned_flag),
                "returned_date": actual_return
            })
        students.append(student)
    conn.close()
    return students


def save_students(students):
    print("[DEBUG] save_students called, students list:", students)
    conn = get_connection()
    cursor = conn.cursor()
    # Get existing students
    cursor.execute("SELECT id FROM students")
    existing_ids = {row["id"] for row in cursor.fetchall()}
    new_ids = set()
    for student in students:
        # Upsert student
        if "id" in student and student["id"] in existing_ids:
            cursor.execute(
                """
                UPDATE students SET last_name=?, first_name=?, class=?, parallel=? WHERE id=?
                """,
                (student["last_name"], student["first_name"], student["class"], student["parallel"], student["id"])
            )
            sid = student["id"]
        else:
            cursor.execute(
                "INSERT INTO students (last_name, first_name, middle_name, class, parallel) VALUES (?, ?, ?, ?, ?)",
                (student["last_name"], student["first_name"], "", student["class"], student["parallel"])
            )
            sid = cursor.lastrowid
            student["id"] = sid
        new_ids.add(sid)

        # Reset student_books
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))
        # Insert new book entries
        for book_entry in student.get("books", []):
            title_author = book_entry.get("book", "").strip()
            if not title_author:
                continue
            issue_str = book_entry.get("issue_date", "")
            planned_str = book_entry.get("return_date", "")
            returned_flag = 1 if book_entry.get("returned") else 0
            returned_str = book_entry.get("returned_date", "")
            # Convert to ISO
            qd = QDate.fromString(issue_str, "dd.MM.yyyy")
            due_iso = qd.toString("yyyy-MM-dd") if qd.isValid() else ''
            qp = QDate.fromString(planned_str, "dd.MM.yyyy")
            planned_iso = qp.toString("yyyy-MM-dd") if qp.isValid() else ''
            qr = QDate.fromString(returned_str, "dd.MM.yyyy")
            returned_iso = qr.toString("yyyy-MM-dd") if qr.isValid() else ''
            # Get or insert book
            cursor.execute("SELECT id FROM books WHERE title || ' - ' || author = ?", (title_author,))
            r = cursor.fetchone()
            if r:
                book_id = r["id"]
            else:
                if " - " in title_author:
                    title, author = title_author.split(" - ", 1)
                else:
                    title, author = title_author, ""
                cursor.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)", (title.strip(), author.strip(), None))
                book_id = cursor.lastrowid
            # Insert into student_books
            cursor.execute(
                """
                INSERT INTO student_books (student_id, book_id, due_date, return_date, returned, returned_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sid, book_id, due_iso, planned_iso, returned_flag, returned_iso)
            )
    # Delete removed students
    for sid in existing_ids - new_ids:
        cursor.execute("DELETE FROM student_books WHERE student_id = ?", (sid,))
        cursor.execute("DELETE FROM students WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
