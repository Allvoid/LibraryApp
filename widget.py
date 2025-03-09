import sys
import os
import json
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDialog, QFormLayout, QMessageBox, QLineEdit, QCompleter, QStyle,
    QSizePolicy, QStackedWidget, QTableWidget, QTableWidgetItem, QListWidget,
    QGroupBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer

# Абсолютные пути для файлов (находятся в той же папке, что и этот файл)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.json")
books_path = os.path.join(BASE_DIR, "литература.txt")
students_path = os.path.join(BASE_DIR, "students.json")

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =============================================================
# Диалог для добавления/редактирования ученика с выбором книг
# =============================================================
class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None, books_list=None, classes_list=None, parallels_list=None):
        super().__init__(parent)
        self.student_data = student_data
        self.books_list = books_list if books_list is not None else []
        self.classes_list = classes_list if classes_list is not None else []
        self.parallels_list = parallels_list if parallels_list is not None else []
        # Каждый элемент хранится как кортеж (container, combo, delete_btn)
        self.book_selectors = []
        self.setWindowTitle("Редактировать ученика" if student_data else "Добавить ученика")
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.last_name_edit = QLineEdit()
        self.last_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.middle_name_edit = QLineEdit()
        self.middle_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addRow("Фамилия:", self.last_name_edit)
        layout.addRow("Имя:", self.first_name_edit)
        layout.addRow("Отчество:", self.middle_name_edit)

        self.class_combo = QComboBox()
        self.class_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.class_combo.addItems(self.classes_list)
        layout.addRow("Класс:", self.class_combo)

        self.parallel_combo = QComboBox()
        self.parallel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.parallel_combo.addItems(self.parallels_list)
        layout.addRow("Параллель:", self.parallel_combo)

        # Область для выбора книг
        self.books_widget = QWidget()
        self.books_layout = QVBoxLayout(self.books_widget)
        self.books_layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow("Книги:", self.books_widget)

        add_book_btn = QPushButton("Добавить книгу")
        add_book_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        add_book_btn.clicked.connect(lambda: self.add_book_selector())
        layout.addRow(add_book_btn)

        if self.student_data:
            self.last_name_edit.setText(self.student_data.get("last_name", ""))
            self.first_name_edit.setText(self.student_data.get("first_name", ""))
            self.middle_name_edit.setText(self.student_data.get("middle_name", ""))
            self.class_combo.setCurrentText(self.student_data.get("class", ""))
            self.parallel_combo.setCurrentText(self.student_data.get("parallel", ""))
            books = self.student_data.get("books", [])
            if books:
                for bk in books:
                    self.add_book_selector(initial_text=bk)
            else:
                self.add_book_selector()
        else:
            self.add_book_selector()

        btn_layout = QHBoxLayout()
        if self.student_data is not None:
            delete_btn = QPushButton("Удалить ученика")
            delete_btn.clicked.connect(lambda: self.done(2))
            btn_layout.addWidget(delete_btn)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить ученика")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)

    def add_book_selector(self, initial_text=""):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        combo = QComboBox()
        combo.setEditable(True)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        combo.addItems(self.books_list)
        completer = QCompleter(self.books_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.setCompleter(completer)
        combo.setCurrentText(initial_text)
        h_layout.addWidget(combo)

        delete_btn = QPushButton()
        trash_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        delete_btn.setIcon(trash_icon)
        delete_btn.setMaximumSize(24, 24)
        delete_btn.setFlat(True)
        h_layout.addWidget(delete_btn)

        # Добавляем кортеж (container, combo, delete_btn)
        self.book_selectors.append((container, combo, delete_btn))
        self.books_layout.addWidget(container)

        # Отложенный вызов удаления для избежания краша
        delete_btn.clicked.connect(lambda: QTimer.singleShot(0, lambda: self.remove_book_selector(container)))
        self.update_delete_buttons()

    def remove_book_selector(self, container):
        for i, (cont, combo, delete_btn) in enumerate(self.book_selectors):
            if cont is container:
                self.book_selectors.pop(i)
                container.setParent(None)
                container.deleteLater()
                break
        self.update_delete_buttons()

    def update_delete_buttons(self):
        count = len(self.book_selectors)
        for (container, combo, delete_btn) in self.book_selectors:
            # Если остается только один выбор, кнопка удаления отключается
            delete_btn.setEnabled(False if count == 1 else True)

    def get_data(self):
        books = [combo.currentText().strip() for (_, combo, _) in self.book_selectors if combo.currentText().strip()]
        return {
            "last_name": self.last_name_edit.text().strip(),
            "first_name": self.first_name_edit.text().strip(),
            "middle_name": self.middle_name_edit.text().strip(),
            "class": self.class_combo.currentText(),
            "parallel": self.parallel_combo.currentText(),
            "books": books
        }


# =============================================================
# Диалог для добавления книги
# =============================================================
class BookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить книгу")
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.title_edit = QLineEdit()
        self.title_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.author_edit = QLineEdit()
        self.author_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addRow("Название:", self.title_edit)
        layout.addRow("Автор:", self.author_edit)
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить книгу")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "Title": self.title_edit.text().strip(),
            "Author": self.author_edit.text().strip()
        }


# =============================================================
# Диалог для обработки неоднозначных учеников при сдвиге
# =============================================================
class AmbiguousShiftDialog(QDialog):
    def __init__(self, ambiguous_students, last_class, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор для неоднозначных учеников")
        self.ambiguous_students = ambiguous_students  # список ссылок на объекты учеников из self.students
        self.last_class = last_class
        self.decisions = {}  # для каждого ученика: "shift" или "delete"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("Для следующих учеников выбор неоднозначен. Выберите действие для каждого:")
        layout.addWidget(info_label)
        self.table = QTableWidget(len(self.ambiguous_students), 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Класс", "Перевести", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row, st in enumerate(self.ambiguous_students):
            fio = f'{st.get("last_name", "")} {st.get("first_name", "")} {st.get("middle_name", "")}'
            self.table.setItem(row, 0, QTableWidgetItem(fio))
            self.table.setItem(row, 1, QTableWidgetItem(st.get("class", "")))
            btn_shift = QPushButton("Перевести")
            btn_delete = QPushButton("Удалить")
            btn_shift.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_delete.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if st.get("class", "") == self.last_class:
                btn_shift.setEnabled(False)
            btn_shift.clicked.connect(lambda checked, r=row: self.set_decision(r, "shift"))
            btn_delete.clicked.connect(lambda checked, r=row: self.on_delete_clicked(r))
            self.table.setCellWidget(row, 2, btn_shift)
            self.table.setCellWidget(row, 3, btn_delete)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(self.on_apply)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        self.check_all_decisions_set()

    def set_decision(self, row, decision):
        self.decisions[row] = decision
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(Qt.GlobalColor.lightGray)
        self.check_all_decisions_set()

    def on_delete_clicked(self, row):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Подтверждение удаления")
        msgBox.setText("Вы уверены, ведь удалиться и долг ученика?")
        yesButton = msgBox.addButton("Да", QMessageBox.ButtonRole.YesRole)
        noButton = msgBox.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        msgBox.exec()
        if msgBox.clickedButton() == yesButton:
            self.set_decision(row, "delete")

    def check_all_decisions_set(self):
        self.apply_btn.setEnabled(len(self.decisions) == len(self.ambiguous_students))

    def on_apply(self):
        for row, st in enumerate(self.ambiguous_students):
            decision = self.decisions.get(row)
            if decision == "shift":
                if st.get("class", "").isdigit():
                    st["class"] = str(int(st["class"]) + 1)
            elif decision == "delete":
                st["to_delete"] = True
        self.accept()


# =============================================================
# Главный класс приложения
# =============================================================
class LibraryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Школьная библиотека")
        self.setGeometry(100, 100, 900, 600)
        self.config = self.load_config()
        self.books = self.load_books()
        self.students = self.load_students()

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
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.fio_search = QLineEdit()
        self.fio_search.setPlaceholderText("Введите ФИО...")
        self.fio_search.textChanged.connect(lambda: self.on_filters_changed())
        search_layout.addWidget(self.fio_search)
        layout.addLayout(search_layout)

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
        self.class_filter.currentTextChanged.connect(lambda: self.on_filters_changed())
        self.parallel_filter.currentTextChanged.connect(lambda: self.on_filters_changed())
        layout.addLayout(filters_layout)

        add_student_btn = QPushButton("Добавить ученика")
        add_student_btn.clicked.connect(self.add_student)
        layout.addWidget(add_student_btn)

        self.readers_table = QTableWidget(0, 7)
        self.readers_table.setHorizontalHeaderLabels(["Id", "Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги"])
        self.readers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.readers_table.doubleClicked.connect(self.edit_student)
        layout.addWidget(self.readers_table)

        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.readers_status_label = QLabel("Читателей: 0/0")
        status_layout.addWidget(self.readers_status_label)
        layout.addLayout(status_layout)

        return page

    def on_filters_changed(self):
        self.lazy_cancelled = True
        self.start_lazy_loading_readers(reset_books=False)

    def start_lazy_loading_readers(self, reset_books=True):
        self.lazy_cancelled = False
        self.lazy_readers_data = self.get_filtered_students()
        self.current_reader_index = 0
        self.total_readers = len(self.lazy_readers_data)
        self.readers_table.setRowCount(0)
        self.readers_loaded = False
        self.update_readers_status()
        self.load_next_readers_chunk(reset_books=reset_books)

    def load_next_readers_chunk(self, reset_books=True):
        if self.lazy_cancelled:
            return
        CHUNK_SIZE = 50
        end_index = min(self.current_reader_index + CHUNK_SIZE, self.total_readers)
        for i in range(self.current_reader_index, end_index):
            row = self.readers_table.rowCount()
            self.insert_student_in_table(row, self.lazy_readers_data[i])
        self.current_reader_index = end_index
        self.update_readers_status()
        if self.current_reader_index < self.total_readers and not self.lazy_cancelled:
            QTimer.singleShot(60, lambda: self.load_next_readers_chunk(reset_books=reset_books))
        else:
            self.readers_loaded = True
            if reset_books and (not self.books_loaded):
                self.start_lazy_loading_books()

    def update_readers_status(self):
        self.readers_status_label.setText(f"Читателей: {self.current_reader_index}/{self.total_readers}")

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
        self.readers_table.setItem(row, 6, QTableWidgetItem(", ".join(data.get("books", []))))

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

        self.books_table = QTableWidget(0, 2)
        self.books_table.setHorizontalHeaderLabels(["Название", "Автор"])
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

        return page

    def on_book_search_text_changed(self):
        self.book_search_timer.start(300)

    def start_lazy_loading_books(self):
        query = self.book_search_edit.text().lower() if hasattr(self, 'book_search_edit') else ""
        self.lazy_books_data = []
        for bk in self.books:
            title = bk.get("Title", "")
            author = bk.get("Author", "")
            if query and (query not in title.lower() and query not in author.lower()):
                continue
            self.lazy_books_data.append(bk)
        self.current_book_index = 0
        self.total_books = len(self.lazy_books_data)
        self.books_table.setRowCount(0)
        self.books_loaded = False
        self.update_books_status()
        self.load_next_books_chunk()

    def load_next_books_chunk(self):
        CHUNK_SIZE = 50
        end_index = min(self.current_book_index + CHUNK_SIZE, self.total_books)
        for i in range(self.current_book_index, end_index):
            row = self.books_table.rowCount()
            book = self.lazy_books_data[i]
            self.books_table.insertRow(row)
            self.books_table.setItem(row, 0, QTableWidgetItem(book.get("Title", "")))
            self.books_table.setItem(row, 1, QTableWidgetItem(book.get("Author", "")))
        self.current_book_index = end_index
        self.update_books_status()
        if self.current_book_index < self.total_books:
            QTimer.singleShot(60, self.load_next_books_chunk)
        else:
            self.books_loaded = True

    def update_books_status(self):
        self.books_status_label.setText(f"Книг: {self.current_book_index}/{self.total_books}")

    def add_book(self):
        dlg = BookDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data["Title"] and data["Author"]:
                self.books.append(data)
                self.save_books()
                self.start_lazy_loading_books()
            else:
                QMessageBox.warning(self, "Ошибка", "Оба поля должны быть заполнены!")

    def delete_book(self):
        selected = self.books_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления!")
            return
        row = selected[0].row()
        query = self.book_search_edit.text().lower()
        filtered = [b for b in self.books if (not query) or (query in b.get("Title", "").lower() or query in b.get("Author", "").lower())]
        if row < len(filtered):
            book_to_delete = filtered[row]
            self.books.remove(book_to_delete)
            self.save_books()
            self.start_lazy_loading_books()

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
        self.save_config()
        self.class_filter.clear()
        self.class_filter.addItem("Все")
        self.class_filter.addItems(classes)
        self.parallel_filter.clear()
        self.parallel_filter.addItem("Все")
        self.parallel_filter.addItems(parallels)
        QMessageBox.information(self, "Сохранено", "Настройки сохранены.")

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
            self.students.append(data)
            self.save_students()
            self.start_lazy_loading_readers(reset_books=False)

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
            self.save_students()
            self.start_lazy_loading_readers(reset_books=False)
        elif res == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not self.validate_student_data(data):
                return
            self.students[full_index] = data
            self.save_students()
            self.start_lazy_loading_readers(reset_books=False)

    def validate_student_data(self, data):
        if (not self.is_valid_name(data["last_name"]) or
            not self.is_valid_name(data["first_name"]) or
            not self.is_valid_name(data["middle_name"])):
            QMessageBox.warning(self, "Ошибка ввода", "Фамилия, Имя и Отчество должны содержать только буквы!")
            return False
        return True

    @staticmethod
    def is_valid_name(text):
        return bool(re.fullmatch(r"[А-Яа-яA-Za-z-]+", text.strip()))

    def get_books_display_list(self):
        return [f'{b.get("Title", "")} - {b.get("Author", "")}' for b in self.books]

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
        self.save_students()
        self.start_lazy_loading_readers(reset_books=False)

    def load_config(self):
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Ошибка загрузки config.json:", e)
        return {
            "classes": [str(i) for i in range(1, 12)],
            "parallels": ["А", "Б", "В", "Г", "Д", "Л", "М"]
        }

    def save_config(self):
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Ошибка сохранения config.json:", e)

    def load_books(self):
        books = []
        if os.path.exists(books_path):
            try:
                with open(books_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip().rstrip(',')
                        m = re.search(r'\{Title\s*=\s*"([^"]+)"\s*,\s*Author\s*=\s*"([^"]+)"\}', line)
                        if m:
                            books.append({"Title": m.group(1), "Author": m.group(2)})
            except Exception as e:
                print("Ошибка загрузки литература.txt:", e)
        return books

    def save_books(self):
        try:
            with open(books_path, "w", encoding="utf-8") as f:
                for book in self.books:
                    line = f'{{Title = "{book.get("Title", "")}", Author = "{book.get("Author", "")}"}},\n'
                    f.write(line)
        except Exception as e:
            print("Ошибка сохранения литература.txt:", e)

    def load_students(self):
        if os.path.exists(students_path):
            try:
                with open(students_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Ошибка загрузки students.json:", e)
        return []

    def save_students(self):
        try:
            with open(students_path, "w", encoding="utf-8") as f:
                json.dump(self.students, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Ошибка сохранения students.json:", e)

    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())
