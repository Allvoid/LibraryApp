# library_app.py
import sys
import re
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QMessageBox, QDialog
)
from data.config_manager import load_config, save_config
from pages.readers_page import ReadersPage
from pages.books_page import BooksPage
from pages.config_page import ConfigPage
from data.books_manager import load_books, save_books
from data.students_manager import load_students, save_students
from utils import is_valid_name, check_issued_limits

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

class LibraryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Школьная библиотека")
        # Увеличенный размер окна
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1200, 800)

        # Загружаем данные
        self.config = load_config()
        self.books = load_books()
        self.students = load_students()
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        self.menu_buttons = []
        menu_layout = QVBoxLayout()
        button_names = [("Читатели", 0), ("Книги", 1), ("Классы и параллели", 2)]
        for name, index in button_names:
            btn = QPushButton(name)
            btn.setFixedSize(150, 40)
            btn.clicked.connect(lambda _, i=index: self.switch_page(i))
            self.menu_buttons.append(btn)
            menu_layout.addWidget(btn)
        menu_layout.addStretch()
        main_layout.addLayout(menu_layout)

        self.pages = QStackedWidget()
        self.readers_page = ReadersPage(self)
        self.books_page = BooksPage(self)
        self.config_page = ConfigPage(self)
        self.pages.addWidget(self.readers_page)
        self.pages.addWidget(self.books_page)
        self.pages.addWidget(self.config_page)
        main_layout.addWidget(self.pages)
        self.switch_page(0)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setStyleSheet(
                "background-color: lightblue; font-weight: bold;" if i == index else ""
            )

    def add_student(self):
        from dialogs.student_dialog import StudentDialog
        dlg = StudentDialog(
            parent=self,
            student_data=None,
            books_list=self.get_books_display_list(),
            classes_list=self.config.get("classes", []),
            parallels_list=self.config.get("parallels", [])
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not self.validate_student_data(data):
                return
            valid, msg = check_issued_limits(data, self.students, self.books)
            if not valid:
                QMessageBox.warning(self, "Ошибка", msg)
                return
            self.students.append(data)
            save_students(self.students)
            self.students = load_students()
            self.readers_page.reset_lazy_loading()
            self.readers_page.refresh()

    def edit_student(self, index):
        filtered = self.readers_page.get_filtered_students(full=True)
        row = index.row()
        if row >= len(filtered):
            return
        student = filtered[row]
        from dialogs.student_dialog import StudentDialog
        dlg = StudentDialog(
            parent=self,
            student_data=student,
            books_list=self.get_books_display_list(),
            classes_list=self.config.get("classes", []),
            parallels_list=self.config.get("parallels", [])
        )
        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            new_data = dlg.get_data()
            if not self.validate_student_data(new_data):
                return
            valid, msg = check_issued_limits(
                new_data, self.students, self.books, exclude_student=student
            )
            if not valid:
                QMessageBox.warning(self, "Ошибка", msg)
                return
            idx = self.students.index(student)
            self.students[idx] = new_data
            save_students(self.students)
            self.students = load_students()
            self.readers_page.reset_lazy_loading()
            self.readers_page.refresh()
        elif res == 2:
            # Удалить
            self.students.remove(student)
            save_students(self.students)
            self.students = load_students()
            self.readers_page.reset_lazy_loading()
            self.readers_page.refresh()

    def clear_all_students(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы действительно хотите очистить всех учеников?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.button(QMessageBox.StandardButton.Yes).setText("Да")
        msg_box.button(QMessageBox.StandardButton.No).setText("Нет")
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.students = []
            save_students(self.students)
            self.students = load_students()
            self.readers_page.reset_lazy_loading()
            self.readers_page.refresh()

    def add_book(self):
        from dialogs.book_dialog import BookDialog
        dlg = BookDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data["Title"] and data["Author"]:
                self.books.append(data)
                save_books(self.books)
                self.books = load_books()
                self.update_books_table()
            else:
                QMessageBox.warning(
                    self, "Ошибка", "Поля «Название» и «Автор» должны быть заполнены!"
                )

    def delete_book(self):
        indexes = self.books_page.books_table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления!")
            return
        row = indexes[0].row()
        query = self.books_page.book_search_edit.text().lower()
        filtered = [
            bk for bk in self.books
            if not query or (query in bk.get("Title", "").lower() or query in bk.get("Author", "").lower())
        ]
        if row < len(filtered):
            book_to_delete = filtered[row]
            self.books.remove(book_to_delete)
            save_books(self.books)
            self.books = load_books()
            self.update_books_table()

    def clear_all_books(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы действительно хотите удалить все книги?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.button(QMessageBox.StandardButton.Yes).setText("Да")
        msg_box.button(QMessageBox.StandardButton.No).setText("Нет")
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.books = []
            save_books(self.books)
            self.books = load_books()
            self.update_books_table()

    def shift_students(self):
        last_class = max(self.config.get("classes", []), key=lambda x: int(x))
        ambiguous_students = []
        for st in self.students:
            cls = st.get("class", "")
            if not cls.isdigit():
                continue
            if cls not in ["9", last_class]:
                st["class"] = str(int(cls) + 1)
            else:
                ambiguous_students.append(st)
        if ambiguous_students:
            from dialogs.ambiguous_shift_dialog import AmbiguousShiftDialog
            dlg = AmbiguousShiftDialog(ambiguous_students, last_class, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.students = [st for st in self.students if not st.get("to_delete", False)]
        save_students(self.students)
        self.students = load_students()
        self.readers_page.reset_lazy_loading()
        self.readers_page.refresh()

    def add_class(self):
        new_class = self.config_page.new_class_edit.text().strip()
        if new_class and new_class not in self.config.get("classes", []):
            self.config["classes"].append(new_class)
            save_config(self.config)
            self.config_page.refresh()
            self.readers_page.refresh()
            self.config_page.new_class_edit.clear()

    def delete_class(self):
        selected = self.config_page.classes_list_widget.selectedItems()
        if selected:
            for item in selected:
                cls = item.text()
                if cls in self.config.get("classes", []):
                    self.config["classes"].remove(cls)
            save_config(self.config)
            self.config_page.refresh()
            self.readers_page.refresh()

    def add_parallel(self):
        new_parallel = self.config_page.new_parallel_edit.text().strip()
        if new_parallel and new_parallel not in self.config.get("parallels", []):
            self.config["parallels"].append(new_parallel)
            save_config(self.config)
            self.config_page.refresh()
            self.readers_page.refresh()
            self.config_page.new_parallel_edit.clear()

    def delete_parallel(self):
        selected = self.config_page.parallels_list_widget.selectedItems()
        if selected:
            for item in selected:
                par = item.text()
                if par in self.config.get("parallels", []):
                    self.config["parallels"].remove(par)
            save_config(self.config)
            self.config_page.refresh()
            self.readers_page.refresh()

    def update_books_table(self):
        self.books_page.current_books_loaded = self.books_page.books_page_size
        self.books_page.refresh()

    def get_books_display_list(self):
        return [f'{b.get("Title", "")} - {b.get("Author", "")}' for b in self.books]

    def validate_student_data(self, data):
            if not (data["last_name"] and is_valid_name(data["last_name"])):
                QMessageBox.warning(self, "Ошибка ввода", "Фамилия должна содержать только буквы!")
                return False
            if not (data["first_name"] and is_valid_name(data["first_name"])):
                QMessageBox.warning(self, "Ошибка ввода", "Имя должно содержать только буквы!")
                return False
            return True

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())
