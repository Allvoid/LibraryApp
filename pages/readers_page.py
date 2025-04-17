# pages/readers_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import QTimer, QDate
from PyQt6.QtGui import QResizeEvent

# Copyright 2025 Your Name
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License on an "AS IS" BASIS,
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
        # Авто‑таймер ленивой подгрузки
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
        filters_layout.addWidget(QLabel("Сортировать по дате выдачи:"))
        self.due_date_filter = QComboBox()
        self.due_date_filter.addItems(["Все", "Ранние", "Поздние"])
        filters_layout.addWidget(self.due_date_filter)
        self.class_filter.currentTextChanged.connect(self.on_filters_changed)
        self.parallel_filter.currentTextChanged.connect(self.on_filters_changed)
        self.due_date_filter.currentTextChanged.connect(self.on_filters_changed)
        layout.addLayout(filters_layout)
        # Кнопки
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
            ["Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги", "Дата выдачи"]
        )
        self.readers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.readers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.readers_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.readers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.readers_table.doubleClicked.connect(self.app.edit_student)
        layout.addWidget(self.readers_table)
        # Автозагрузка при скролле
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

    def reset_lazy_loading(self):
        """Для совместимости с вызовом из LibraryApp.add_student."""
        self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def on_filters_changed(self):
        current_fio = self.fio_search.text().lower()
        if current_fio != self.prev_fio:
            self.prev_fio = current_fio
            self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def on_readers_scroll(self, value):
        scrollbar = self.readers_table.verticalScrollBar()
        if value == scrollbar.maximum():
            self.load_more()

    def load_more(self):
        if self.loading:
            return
        self.loading = True
        full = self.get_filtered_students(full=True)
        if self.current_readers_loaded < len(full):
            self.current_readers_loaded += self.readers_page_size
            if self.current_readers_loaded > len(full):
                self.current_readers_loaded = len(full)
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
            if fio_query and not (
                fio_query in st.get("last_name", "").lower() or
                fio_query in st.get("first_name", "").lower() or
                fio_query in st.get("middle_name", "").lower()
            ):
                continue
            filtered.append(st)
        # Сортировка по дате выдачи
        if self.due_date_filter.currentText() == "Ранние":
            filtered.sort(key=lambda s: min(
                [QDate.fromString(b["due_date"], "dd.MM.yyyy") for b in s.get("books", [])
                 if QDate.fromString(b["due_date"], "dd.MM.yyyy").isValid()] or [QDate.currentDate()]
            ))
        elif self.due_date_filter.currentText() == "Поздние":
            filtered.sort(key=lambda s: max(
                [QDate.fromString(b["due_date"], "dd.MM.yyyy") for b in s.get("books", [])
                 if QDate.fromString(b["due_date"], "dd.MM.yyyy").isValid()] or [QDate.currentDate()]
            ), reverse=True)
        return filtered if full else filtered[:self.current_readers_loaded]

    def refresh(self):
        full = self.get_filtered_students(full=True)
        part = self.get_filtered_students(full=False)
        self.readers_table.setRowCount(0)
        for st in part:
            row = self.readers_table.rowCount()
            self.readers_table.insertRow(row)
            self.set_student_row(row, st)
        self.readers_status_label.setText(f"Читателей: {len(part)}/{len(full)}")

    def check_and_load_more(self):
        if self.current_readers_loaded < len(self.get_filtered_students(full=True)):
            self.load_more()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.check_and_load_more)

    def set_student_row(self, row, data):
        self.readers_table.setItem(row, 0, QTableWidgetItem(data["last_name"]))
        self.readers_table.setItem(row, 1, QTableWidgetItem(data["first_name"]))
        self.readers_table.setItem(row, 2, QTableWidgetItem(data.get("middle_name", "")))
        self.readers_table.setItem(row, 3, QTableWidgetItem(data["class"]))
        self.readers_table.setItem(row, 4, QTableWidgetItem(data["parallel"]))
        books = [b["book"] for b in data.get("books", [])]
        dates = [b["due_date"] for b in data.get("books", [])]
        self.readers_table.setItem(row, 5, QTableWidgetItem(", ".join(books)))
        self.readers_table.setItem(row, 6, QTableWidgetItem(", ".join(dates)))
