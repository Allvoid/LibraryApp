import sys
import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QDialog,
    QFormLayout, QMessageBox, QLineEdit, QCompleter, QStyle, QSizePolicy,
    QStackedWidget, QTableWidget, QTableWidgetItem, QListWidget, QGroupBox,
    QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QColor

# Импорт диалогов
from dialogs.student_dialog import StudentDialog
from dialogs.book_dialog import BookDialog
from dialogs.ambiguous_shift_dialog import AmbiguousShiftDialog

# Импорт менеджеров данных
from data.config_manager import load_config, save_config
from data.books_manager import load_books, save_books
from data.students_manager import load_students, save_students

# Импорт утилит
from utils import is_valid_name, count_issued, check_issued_limits

class LibraryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Школьная библиотека")
        self.setGeometry(100, 100, 900, 600)
        self.config = load_config()
        self.books = load_books()
        self.students = load_students()

        self.readers_loaded = False
        self.books_loaded = False
        self.lazy_cancelled = False

        self.lazy_readers_data = []
        self.current_reader_index = 0
        self.total_readers = 0
        self.lazy_books_data = []
        self.current_book_index = 0
        self.total_books = 0

        self.book_search_timer = QTimer(self)
        self.book_search_timer.setSingleShot(True)
        self.book_search_timer.timeout.connect(self.start_lazy_loading_books)

        self._init_ui()
        self.start_lazy_loading_readers()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        self.menu_buttons = []
        menu_layout = QVBoxLayout()
        for name, index in [("Читатели", 0), ("Книги", 1), ("Классы и параллели", 2)]:
            btn = QPushButton(name)
            btn.setFixedSize(150, 40)
            btn.clicked.connect(lambda _, i=index: self.switch_page(i))
            self.menu_buttons.append(btn)
            menu_layout.addWidget(btn)
        menu_layout.addStretch()
        main_layout.addLayout(menu_layout)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_readers_page())
        self.pages.addWidget(self.create_books_page())
        self.pages.addWidget(self.create_config_page())
        main_layout.addWidget(self.pages)
        self.switch_page(0)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setStyleSheet("background-color: lightblue; font-weight: bold;" if i == index else "")

    def create_readers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        # Верхняя панель поиска
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.fio_search = QLineEdit()
        self.fio_search.setPlaceholderText("Введите ФИО...")
        self.fio_search.textChanged.connect(lambda: self.on_filters_changed())
        search_layout.addWidget(self.fio_search)
        layout.addLayout(search_layout)

        # Панель фильтров
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Класс:"))
        self.class_filter = QComboBox()
        self.class_filter.addItem("Все")
        self.class_filter.addItems(self.config.get("classes", []))
        filters_layout.addWidget(self.class_filter)
        filters_layout.addWidget(QLabel("Параллель:"))
        self.parallel_filter = QComboBox()
        self.parallel_filter.addItem("Все")
        self.parallel_filter.addItems(self.config.get("parallels", []))
        filters_layout.addWidget(self.parallel_filter)
        filters_layout.addWidget(QLabel("Сортировать по дате сдачи:"))
        self.due_date_filter = QComboBox()
        self.due_date_filter.addItems(["Все", "Сдать раньше", "Сдать позже"])
        filters_layout.addWidget(self.due_date_filter)
        self.class_filter.currentTextChanged.connect(lambda: self.on_filters_changed())
        self.parallel_filter.currentTextChanged.connect(lambda: self.on_filters_changed())
        self.due_date_filter.currentTextChanged.connect(lambda: self.on_filters_changed())
        layout.addLayout(filters_layout)

        # Панель кнопок
        button_layout = QHBoxLayout()
        add_student_btn = QPushButton("Добавить ученика")
        add_student_btn.clicked.connect(self.add_student)
        button_layout.addWidget(add_student_btn)
        clear_all_btn = QPushButton("Очистить всех")
        clear_all_btn.clicked.connect(self.clear_all_students)
        button_layout.addWidget(clear_all_btn)
        layout.addLayout(button_layout)

        # Таблица учеников
        self.readers_table = QTableWidget(0, 8)
        self.readers_table.setHorizontalHeaderLabels(
            ["Id", "Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги", "Срок сдачи"]
        )
        self.readers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.readers_table.doubleClicked.connect(self.edit_student)
        layout.addWidget(self.readers_table)

        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.readers_status_label = QLabel("Читателей: 0/0")
        status_layout.addWidget(self.readers_status_label)
        layout.addLayout(status_layout)

        return page

    def clear_all_students(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы действительно хотите очистить всех учеников?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        no_button = msg_box.button(QMessageBox.StandardButton.No)
        yes_button.setText("Да")
        no_button.setText("Нет")
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Yes.value:
            self.students = []
            save_students(self.students)
            self.start_lazy_loading_readers()

    def on_filters_changed(self):
        self.lazy_cancelled = True
        self.start_lazy_loading_readers()

    def start_lazy_loading_readers(self):
        self.lazy_cancelled = False
        self.lazy_readers_data = self.get_filtered_students()
        self.readers_table.setRowCount(0)
        for student in self.lazy_readers_data:
            self.insert_student_in_table(self.readers_table.rowCount(), student)
        self.update_readers_status()

    def update_readers_status(self):
        total = len(self.get_filtered_students())
        self.readers_status_label.setText(f"Читателей: {self.readers_table.rowCount()}/{total}")

    def get_filtered_students(self):
        selected_class = self.class_filter.currentText()
        selected_parallel = self.parallel_filter.currentText()
        fio_query = self.fio_search.text().lower()
        filtered = []
        for st in self.students:
            if selected_class != "Все" and st.get("class", "") != selected_class:
                continue
            if selected_parallel != "Все" and st.get("parallel", "") != selected_parallel:
                continue
            if fio_query:
                if not (fio_query in st.get("last_name", "").lower() or
                        fio_query in st.get("first_name", "").lower() or
                        fio_query in st.get("middle_name", "").lower()):
                    continue
            filtered.append(st)
        sort_option = self.due_date_filter.currentText()
        if sort_option == "Сдать раньше":
            def sort_key(student):
                dates = [QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy")
                         for b in student.get("books", [])
                         if isinstance(b, dict) and QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy").isValid()]
                return min(dates) if dates else QDate(9999, 12, 31)
            filtered.sort(key=sort_key)
        elif sort_option == "Сдать позже":
            def sort_key(student):
                dates = [QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy")
                         for b in student.get("books", [])
                         if isinstance(b, dict) and QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy").isValid()]
                return max(dates) if dates else QDate(1900, 1, 1)
            filtered.sort(key=sort_key, reverse=True)
        return filtered

    def insert_student_in_table(self, row, data):
        self.readers_table.insertRow(row)
        self.set_student_row(row, data)

    def set_student_row(self, row, data):
        self.readers_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.readers_table.setItem(row, 1, QTableWidgetItem(data["last_name"]))
        self.readers_table.setItem(row, 2, QTableWidgetItem(data["first_name"]))
        self.readers_table.setItem(row, 3, QTableWidgetItem(data["middle_name"]))
        self.readers_table.setItem(row, 4, QTableWidgetItem(data["class"]))
        self.readers_table.setItem(row, 5, QTableWidgetItem(data["parallel"]))
        book_names = []
        due_dates = []
        overdue = False
        current_date = QDate.currentDate()
        for b in data.get("books", []):
            if isinstance(b, dict):
                book_names.append(b.get("book", ""))
                due_date_str = b.get("due_date", "")
                due_dates.append(due_date_str)
                d = QDate.fromString(due_date_str, "dd.MM.yyyy")
                if d.isValid() and d < current_date:
                    overdue = True
        self.readers_table.setItem(row, 6, QTableWidgetItem(", ".join(book_names)))
        self.readers_table.setItem(row, 7, QTableWidgetItem(", ".join(due_dates)))
        if overdue:
            for col in range(self.readers_table.columnCount()):
                item = self.readers_table.item(row, col)
                if item:
                    item.setBackground(QColor("red"))

    def create_books_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        self.book_search_edit = QLineEdit()
        self.book_search_edit.setPlaceholderText("Искать по названию или автору...")
        self.book_search_edit.textChanged.connect(self.on_book_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.book_search_edit)
        layout.addLayout(search_layout)
        self.books_table = QTableWidget(0, 3)
        self.books_table.setHorizontalHeaderLabels(["Название", "Автор", "Количество"])
        self.books_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.books_table)
        btn_layout = QHBoxLayout()
        add_book_btn = QPushButton("Добавить книгу")
        add_book_btn.clicked.connect(self.add_book)
        del_book_btn = QPushButton("Удалить книгу")
        del_book_btn.clicked.connect(self.delete_book)
        btn_layout.addWidget(add_book_btn)
        btn_layout.addWidget(del_book_btn)
        layout.addLayout(btn_layout)
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.books_status_label = QLabel("Книг: 0/0")
        status_layout.addWidget(self.books_status_label)
        layout.addLayout(status_layout)
        self.update_books_table()  # Обновляем таблицу при создании страницы
        return page

    def on_book_search_text_changed(self):
        self.update_books_table()

    def update_books_table(self):
        query = self.book_search_edit.text().lower() if hasattr(self, 'book_search_edit') else ""
        filtered = [bk for bk in self.books if (not query) or (query in bk.get("Title", "").lower() or query in bk.get("Author", "").lower())]
        self.books_table.setRowCount(0)
        for bk in filtered:
            row = self.books_table.rowCount()
            self.books_table.insertRow(row)
            self.books_table.setItem(row, 0, QTableWidgetItem(bk.get("Title", "")))
            self.books_table.setItem(row, 1, QTableWidgetItem(bk.get("Author", "")))
            quantity = bk.get("quantity")
            self.books_table.setItem(row, 2, QTableWidgetItem(str(quantity) if quantity is not None else ""))
        self.total_books = len(filtered)
        self.update_books_status()

    def start_lazy_loading_books(self):
        self.update_books_table()

    def update_books_status(self):
        self.books_status_label.setText(f"Книг: {self.total_books}/{len(self.books)}")

    def add_book(self):
        dlg = BookDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data["Title"] and data["Author"]:
                self.books.append(data)
                save_books(self.books)
                self.books = load_books()
                self.update_books_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Поля «Название» и «Автор» должны быть заполнены!")

    def delete_book(self):
        selected = self.books_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления!")
            return
        row = selected[0].row()
        query = self.book_search_edit.text().lower()
        filtered = [bk for bk in self.books if (not query) or (query in bk.get("Title", "").lower() or query in bk.get("Author", "").lower())]
        if row < len(filtered):
            book_to_delete = filtered[row]
            self.books.remove(book_to_delete)
            save_books(self.books)
            self.books = load_books()
            self.update_books_table()

    def create_config_page(self):
        page = QWidget()
        outer_layout = QVBoxLayout(page)
        main_layout = QHBoxLayout()
        classes_group = QGroupBox("Классы")
        classes_layout = QVBoxLayout(classes_group)
        self.classes_list_widget = QListWidget()
        self.classes_list_widget.addItems(self.config.get("classes", []))
        classes_layout.addWidget(self.classes_list_widget)
        add_class_layout = QHBoxLayout()
        self.new_class_edit = QLineEdit()
        self.new_class_edit.setPlaceholderText("Новый класс")
        add_class_btn = QPushButton("Добавить")
        add_class_btn.clicked.connect(self.add_class)
        add_class_layout.addWidget(self.new_class_edit)
        add_class_layout.addWidget(add_class_btn)
        classes_layout.addLayout(add_class_layout)
        del_class_btn = QPushButton("Удалить выбранное")
        del_class_btn.clicked.connect(self.delete_class)
        classes_layout.addWidget(del_class_btn)
        classes_layout.addStretch()

        parallels_group = QGroupBox("Параллели")
        parallels_layout = QVBoxLayout(parallels_group)
        self.parallels_list_widget = QListWidget()
        self.parallels_list_widget.addItems(self.config.get("parallels", []))
        parallels_layout.addWidget(self.parallels_list_widget)
        add_parallel_layout = QHBoxLayout()
        self.new_parallel_edit = QLineEdit()
        self.new_parallel_edit.setPlaceholderText("Новая параллель")
        add_parallel_btn = QPushButton("Добавить")
        add_parallel_btn.clicked.connect(self.add_parallel)
        add_parallel_layout.addWidget(self.new_parallel_edit)
        add_parallel_layout.addWidget(add_parallel_btn)
        parallels_layout.addLayout(add_parallel_layout)
        del_parallel_btn = QPushButton("Удалить выбранное")
        del_parallel_btn.clicked.connect(self.delete_parallel)
        parallels_layout.addWidget(del_parallel_btn)
        parallels_layout.addStretch()

        main_layout.addWidget(classes_group)
        main_layout.addWidget(parallels_group)
        outer_layout.addLayout(main_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        shift_btn = QPushButton("Сдвинуть учеников на следующий класс")
        shift_btn.clicked.connect(self.shift_students)
        bottom_layout.addWidget(shift_btn)
        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_config_changes)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addStretch()
        outer_layout.addLayout(bottom_layout)

        return page

    def add_class(self):
        text = self.new_class_edit.text().strip()
        if text and text not in [self.classes_list_widget.item(i).text() for i in range(self.classes_list_widget.count())]:
            self.classes_list_widget.addItem(text)
            self.new_class_edit.clear()

    def delete_class(self):
        for item in self.classes_list_widget.selectedItems():
            self.classes_list_widget.takeItem(self.classes_list_widget.row(item))

    def add_parallel(self):
        text = self.new_parallel_edit.text().strip()
        if text and text not in [self.parallels_list_widget.item(i).text() for i in range(self.parallels_list_widget.count())]:
            self.parallels_list_widget.addItem(text)
            self.new_parallel_edit.clear()

    def delete_parallel(self):
        for item in self.parallels_list_widget.selectedItems():
            self.parallels_list_widget.takeItem(self.parallels_list_widget.row(item))

    def save_config_changes(self):
        classes = [self.classes_list_widget.item(i).text().strip() for i in range(self.classes_list_widget.count())]
        parallels = [self.parallels_list_widget.item(i).text().strip() for i in range(self.parallels_list_widget.count())]
        if not classes or not parallels:
            QMessageBox.warning(self, "Ошибка", "Списки не могут быть пустыми!")
            return
        self.config["classes"] = classes
        self.config["parallels"] = parallels
        save_config(self.config)
        self.class_filter.clear()
        self.class_filter.addItem("Все")
        self.class_filter.addItems(classes)
        self.parallel_filter.clear()
        self.parallel_filter.addItem("Все")
        self.parallel_filter.addItems(parallels)
        QMessageBox.information(self, "Сохранено", "Настройки сохранены.")

    def count_issued(self, book_str, exclude_student=None):
        count = 0
        for st in self.students:
            if exclude_student is not None and st is exclude_student:
                continue
            for b in st.get("books", []):
                if isinstance(b, dict) and b.get("book", "") == book_str:
                    count += 1
        return count

    def add_student(self):
        dlg = StudentDialog(
            self,
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
            if self.filter_student(data):
                pos = self.compute_sorted_position(data)
                self.insert_student_in_table(pos, data)
                self.total_readers = len(self.get_filtered_students())
                self.update_readers_status()

    def edit_student(self, index):
        row = index.row()
        filtered = self.get_filtered_students()
        if row >= len(filtered):
            return
        student = filtered[row]
        full_index = self.students.index(student)
        dlg = StudentDialog(
            self,
            student_data=student,
            books_list=self.get_books_display_list(),
            classes_list=self.config.get("classes", []),
            parallels_list=self.config.get("parallels", [])
        )
        res = dlg.exec()
        if res == 2:
            del self.students[full_index]
            save_students(self.students)
            self.readers_table.removeRow(row)
            self.total_readers = len(self.get_filtered_students())
            self.update_readers_status()
        elif res == QDialog.DialogCode.Accepted:
            new_data = dlg.get_data()
            if not self.validate_student_data(new_data):
                return
            valid, msg = check_issued_limits(new_data, self.students, self.books, exclude_student=student)
            if not valid:
                QMessageBox.warning(self, "Ошибка", msg)
                return
            self.students[full_index] = new_data
            save_students(self.students)
            self.set_student_row(row, new_data)

    def validate_student_data(self, data):
        if (not self.is_valid_name(data["last_name"]) or
            not self.is_valid_name(data["first_name"]) or
            not self.is_valid_name(data["middle_name"])):
            QMessageBox.warning(self, "Ошибка ввода", "Фамилия, Имя и Отчество должны содержать только буквы!")
            return False
        return True

    def is_valid_name(self, text):
        return is_valid_name(text)

    def get_books_display_list(self):
        return [f'{b.get("Title", "")} - {b.get("Author", "")}' for b in self.books]

    def compute_sorted_position(self, new_student):
        filtered = self.get_filtered_students()
        sort_option = self.due_date_filter.currentText()
        if sort_option == "Все":
            return len(filtered)
        new_date = None
        dates = []
        for b in new_student.get("books", []):
            if isinstance(b, dict):
                d = QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy")
                if d.isValid():
                    dates.append(d)
        if dates:
            new_date = min(dates) if sort_option == "Сдать раньше" else max(dates)
        else:
            new_date = QDate(9999, 12, 31) if sort_option == "Сдать раньше" else QDate(1900, 1, 1)
        pos = 0
        for student in filtered:
            dates = []
            for b in student.get("books", []):
                if isinstance(b, dict):
                    d = QDate.fromString(b.get("due_date", ""), "dd.MM.yyyy")
                    if d.isValid():
                        dates.append(d)
            if dates:
                current_date = min(dates) if sort_option == "Сдать раньше" else max(dates)
            else:
                current_date = QDate(9999, 12, 31) if sort_option == "Сдать раньше" else QDate(1900, 1, 1)
            if sort_option == "Сдать раньше":
                if new_date < current_date:
                    break
            else:
                if new_date > current_date:
                    break
            pos += 1
        return pos

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
            dlg = AmbiguousShiftDialog(ambiguous_students, last_class, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.students = [st for st in self.students if not st.get("to_delete", False)]
        save_students(self.students)
        self.start_lazy_loading_readers()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())
