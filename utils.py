import re
from PyQt6.QtCore import QDate

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

def is_valid_name(text):
    return bool(re.fullmatch(r"[А-Яа-яA-Za-z-]+", text.strip()))

def count_issued(book_str, students, exclude_student=None):
    count = 0
    for st in students:
        if exclude_student is not None and st is exclude_student:
            continue
        for b in st.get("books", []):
            if isinstance(b, dict) and b.get("book", "") == book_str:
                count += 1
    return count

def check_issued_limits(new_student, students, books, exclude_student=None):
    new_counts = {}
    for b in new_student.get("books", []):
        book_str = b.get("book", "")
        if book_str:
            new_counts[book_str] = new_counts.get(book_str, 0) + 1
    for book_str, new_count in new_counts.items():
        lib_book = None
        for book in books:
            display_str = f'{book.get("Title", "")} - {book.get("Author", "")}'
            if display_str == book_str:
                lib_book = book
                break
        if lib_book and lib_book.get("quantity") is not None:
            available = int(lib_book.get("quantity"))
            current = count_issued(book_str, students, exclude_student)
            if current + new_count > available:
                return False, f"Недостаточно экземпляров книги: {book_str}\nВыдано: {current}, доступно: {available}"
    return True, ""
