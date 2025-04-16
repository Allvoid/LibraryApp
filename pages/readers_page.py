# pages/readers_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import QDate, QTimer, QEvent
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
        self.loading = False
        self._init_ui()
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

        # Кнопки действия
        btn_layout = QHBoxLayout()
        add_student_btn = QPushButton("Добавить ученика")
        add_student_btn.clicked.connect(self.app.add_student)
        clear_all_btn = QPushButton("Очистить всех")
        clear_all_btn.clicked.connect(self.app.clear_all_students)
        btn_layout.addWidget(add_student_btn)
        btn_layout.addWidget(clear_all_btn)
        layout.addLayout(btn_layout)

        # Таблица читателей
        self.readers_table = QTableWidget(0, 7)
        self.readers_table.setHorizontalHeaderLabels([
            "Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги", "Срок сдачи"
        ])
        self.readers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Отключаем редактирование, выделяем строки
        self.readers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.readers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.readers_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.readers_table.doubleClicked.connect(self.app.edit_student)
        layout.addWidget(self.readers_table)

        # Сброс выделения по клику в пустом месте внутри таблицы
        self.readers_table.viewport().installEventFilter(self)
        # И по клику в любом свободном месте страницы
        self.installEventFilter(self)

        # Автозагрузка при скролле
        self.readers_table.verticalScrollBar().valueChanged.connect(self.on_readers_scroll)

        # Статус
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.readers_status_label = QLabel("Читателей: 0/0")
        status_layout.addWidget(self.readers_status_label)
        layout.addLayout(status_layout)

        # Инициализация данных
        self.prev_fio = self.fio_search.text().lower()
        self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def mousePressEvent(self, event):
        # Если клик вне таблицы — сбросим выделение
        if not self.readers_table.geometry().contains(event.pos()):
            self.readers_table.clearSelection()
        super().mousePressEvent(event)

    def eventFilter(self, source, event):
        # Также ловим клики внутри таблицы пустой области
        if source == self.readers_table.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            if not self.readers_table.indexAt(event.pos()).isValid():
                self.readers_table.clearSelection()
        return super().eventFilter(source, event)

    def on_filters_changed(self):
        current = self.fio_search.text().lower()
        if current != self.prev_fio:
            self.prev_fio = current
            self.current_readers_loaded = self.readers_page_size
        else:
            self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def on_readers_scroll(self, value):
        if value == self.readers_table.verticalScrollBar().maximum():
            self.load_more()

    def load_more(self):
        if self.loading:
            return
        self.loading = True
        full = self.get_filtered_students(full=True)
        if self.current_readers_loaded < len(full):
            self.current_readers_loaded = min(len(full), self.current_readers_loaded + self.readers_page_size)
            self.refresh()
        self.loading = False

    def get_filtered_students(self, full=False):
        selected_class = self.class_filter.currentText()
        selected_parallel = self.parallel_filter.currentText()
        fio_query = self.fio_search.text().lower()
        lst = []
        for st in self.app.students:
            if selected_class != "Все" and st.get("class", "") != selected_class:
                continue
            if selected_parallel != "Все" and st.get("parallel", "") != selected_parallel:
                continue
            if fio_query and not any(fio_query in st.get(k, "").lower() for k in ("last_name", "first_name", "middle_name")):
                continue
            lst.append(st)
        sort_opt = self.due_date_filter.currentText()
        if sort_opt == "Сдать раньше":
            lst.sort(key=lambda s: min(
                [QDate.fromString(b["due_date"], "dd.MM.yyyy") for b in s.get("books", [])
                 if QDate.fromString(b["due_date"], "dd.MM.yyyy").isValid()] or [QDate(9999,12,31)]
            ))
        elif sort_opt == "Сдать позже":
            lst.sort(key=lambda s: max(
                [QDate.fromString(b["due_date"], "dd.MM.yyyy") for b in s.get("books", [])
                 if QDate.fromString(b["due_date"], "dd.MM.yyyy").isValid()] or [QDate(1900,1,1)]
            ), reverse=True)
        return lst if full else lst[:self.current_readers_loaded]

    def refresh(self):
        full = self.get_filtered_students(full=True)
        part = self.get_filtered_students(full=False)
        self.readers_table.setRowCount(0)
        for student in part:
            row = self.readers_table.rowCount()
            self.readers_table.insertRow(row)
            self.set_student_row(row, student)
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
        self.readers_table.setItem(row, 2, QTableWidgetItem(data["middle_name"]))
        self.readers_table.setItem(row, 3, QTableWidgetItem(data["class"]))
        self.readers_table.setItem(row, 4, QTableWidgetItem(data["parallel"]))
        books = [b["book"] for b in data.get("books", [])]
        dates = [b["due_date"] for b in data.get("books", [])]
        self.readers_table.setItem(row, 5, QTableWidgetItem(", ".join(books)))
        self.readers_table.setItem(row, 6, QTableWidgetItem(", ".join(dates)))
        if any(QDate.fromString(d, "dd.MM.yyyy").isValid() and QDate.fromString(d, "dd.MM.yyyy") < QDate.currentDate() for d in dates):
            for col in range(self.readers_table.columnCount()):
                self.readers_table.item(row, col).setBackground(QColor("red"))
