# pages/readers_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import QDate, QTimer
from PyQt6.QtGui import QColor, QResizeEvent

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

class ReadersPage(QWidget):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.readers_page_size = 50
        self.current_readers_loaded = 0
        self.prev_fio = ""
        self.loading = False  # Флаг загрузки
        self._init_ui()
        # Авто-таймер, который каждые 500 мс проверяет необходимость подгрузки
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.check_and_load_more)
        self.auto_timer.start(500)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        # Поисковая панель
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.fio_search = QLineEdit()
        self.fio_search.setPlaceholderText("Введите ФИО...")
        self.fio_search.textChanged.connect(self.on_filters_changed)
        search_layout.addWidget(self.fio_search)
        layout.addLayout(search_layout)
        # Фильтры
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Класс:"))
        self.class_filter = QComboBox()
        self.class_filter.addItem("Все")
        self.class_filter.addItems(self.app.config.get("classes", []))
        filters_layout.addWidget(self.class_filter)
        filters_layout.addWidget(QLabel("Параллель:"))
        self.parallel_filter = QComboBox()
        self.parallel_filter.addItem("Все")
        self.parallel_filter.addItems(self.app.config.get("parallels", []))
        filters_layout.addWidget(self.parallel_filter)
        filters_layout.addWidget(QLabel("Сортировать по дате сдачи:"))
        self.due_date_filter = QComboBox()
        self.due_date_filter.addItems(["Все", "Сдать раньше", "Сдать позже"])
        filters_layout.addWidget(self.due_date_filter)
        self.class_filter.currentTextChanged.connect(self.on_filters_changed)
        self.parallel_filter.currentTextChanged.connect(self.on_filters_changed)
        self.due_date_filter.currentTextChanged.connect(self.on_filters_changed)
        layout.addLayout(filters_layout)
        # Панель кнопок
        btn_layout = QHBoxLayout()
        add_student_btn = QPushButton("Добавить ученика")
        add_student_btn.clicked.connect(self.app.add_student)
        clear_all_btn = QPushButton("Очистить всех")
        clear_all_btn.clicked.connect(self.app.clear_all_students)
        btn_layout.addWidget(add_student_btn)
        btn_layout.addWidget(clear_all_btn)
        layout.addLayout(btn_layout)
        # Таблица учеников
        self.readers_table = QTableWidget(0, 7)
        self.readers_table.setHorizontalHeaderLabels(
            ["Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги", "Срок сдачи"]
        )
        self.readers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.readers_table.doubleClicked.connect(self.app.edit_student)
        # Отключаем встроенное редактирование ячеек
        self.readers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.readers_table)
        # Подключаем автоматическую загрузку по скроллу (на всякий случай)
        self.readers_table.verticalScrollBar().valueChanged.connect(self.on_readers_scroll)
        # Статус
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.readers_status_label = QLabel("Читателей: 0/0")
        status_layout.addWidget(self.readers_status_label)
        layout.addLayout(status_layout)
        # Инициализация
        self.prev_fio = self.fio_search.text().lower()
        self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def on_filters_changed(self):
        current_fio = self.fio_search.text().lower()
        if current_fio != self.prev_fio:
            self.prev_fio = current_fio
            self.current_readers_loaded = self.readers_page_size
        else:
            self.current_readers_loaded = self.readers_page_size  # сброс при изменении фильтров
        self.refresh()

    def on_readers_scroll(self, value):
        scrollbar = self.readers_table.verticalScrollBar()
        if value == scrollbar.maximum():
            self.load_more()

    def load_more(self):
        if self.loading:
            return
        self.loading = True
        filtered_full = self.get_filtered_students(full=True)
        if self.current_readers_loaded < len(filtered_full):
            self.current_readers_loaded += self.readers_page_size
            if self.current_readers_loaded > len(filtered_full):
                self.current_readers_loaded = len(filtered_full)
            self.refresh()
        self.loading = False

    def get_filtered_students(self, full=False):
        selected_class = self.class_filter.currentText()
        selected_parallel = self.parallel_filter.currentText()
        fio_query = self.fio_search.text().lower()
        filtered = []
        for st in self.app.students:
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
        return filtered[:self.current_readers_loaded] if not full else filtered

    def refresh(self):
        filtered_full = self.get_filtered_students(full=True)
        filtered = self.get_filtered_students(full=False)
        self.readers_table.setRowCount(0)
        for student in filtered:
            row = self.readers_table.rowCount()
            self.readers_table.insertRow(row)
            self.set_student_row(row, student)
        total = len(filtered_full)
        loaded = len(filtered)
        self.readers_status_label.setText(f"Читателей: {loaded}/{total}")

    def check_and_load_more(self):
        filtered_full = self.get_filtered_students(full=True)
        if self.current_readers_loaded < len(filtered_full):
            self.load_more()

    def auto_load_more_if_needed(self):
        if self.loading:
            return
        viewport_height = self.readers_table.viewport().height()
        if self.readers_table.rowCount() > 0:
            row_height = self.readers_table.sizeHintForRow(0)
            content_height = row_height * self.readers_table.rowCount()
        else:
            content_height = 0
        filtered_full = self.get_filtered_students(full=True)
        if content_height < viewport_height and self.current_readers_loaded < len(filtered_full):
            self.load_more()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.check_and_load_more)

    def set_student_row(self, row, data):
        self.readers_table.setItem(row, 0, QTableWidgetItem(data["last_name"]))
        self.readers_table.setItem(row, 1, QTableWidgetItem(data["first_name"]))
        self.readers_table.setItem(row, 2, QTableWidgetItem(data["middle_name"]))
        self.readers_table.setItem(row, 3, QTableWidgetItem(data["class"]))
        self.readers_table.setItem(row, 4, QTableWidgetItem(data["parallel"]))
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
        self.readers_table.setItem(row, 5, QTableWidgetItem(", ".join(book_names)))
        self.readers_table.setItem(row, 6, QTableWidgetItem(", ".join(due_dates)))
        if overdue:
            for col in range(self.readers_table.columnCount()):
                item = self.readers_table.item(row, col)
                if item:
                    item.setBackground(QColor("red"))

    def reset_lazy_loading(self):
        self.current_readers_loaded = self.readers_page_size
        self.refresh()
