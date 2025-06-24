# pages/readers_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import QTimer, QDate
from PyQt6.QtGui import QResizeEvent, QColor, QBrush

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
        # Поиск по ФИО
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.fio_search = QLineEdit()
        self.fio_search.setPlaceholderText("Введите ФИО...")
        self.fio_search.textChanged.connect(self.on_filters_changed)
        search_layout.addWidget(self.fio_search)
        layout.addLayout(search_layout)

        # Фильтры и сортировка по дате
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Класс:"))
        self.class_filter = QComboBox()
        self.class_filter.addItem("Все")
        self.class_filter.addItems(self.app.config.get("classes", []))
        self.class_filter.currentTextChanged.connect(self.on_filters_changed)
        filters_layout.addWidget(self.class_filter)
        filters_layout.addWidget(QLabel("Параллель:"))
        self.parallel_filter = QComboBox()
        self.parallel_filter.addItem("Все")
        self.parallel_filter.addItems(self.app.config.get("parallels", []))
        self.parallel_filter.currentTextChanged.connect(self.on_filters_changed)
        filters_layout.addWidget(self.parallel_filter)
        filters_layout.addWidget(QLabel("По дате:"))
        self.due_date_filter = QComboBox()
        self.due_date_filter.addItems([
            "Без сортировки и фильтров",
            "Сортировать по недавним выдачам",
            "Сортировать по старым выдачам",
            "Отобразить только просроченные сдачи",
            "Отобразить только не просроченные сдачи"
        ])
        self.due_date_filter.currentTextChanged.connect(self.on_filters_changed)
        filters_layout.addWidget(self.due_date_filter)
        layout.addLayout(filters_layout)

        # Кнопки управления
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
            "Фамилия", "Имя", "Отчество", "Класс", "Параллель", "Книги", "Даты"
        ])
        header = self.readers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.readers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.readers_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.readers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.readers_table.doubleClicked.connect(self.app.edit_student)
        layout.addWidget(self.readers_table)

        # Статусная строка
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
        self.current_readers_loaded = self.readers_page_size
        self.refresh()

    def on_filters_changed(self):
        current = self.fio_search.text().lower()
        if current != self.prev_fio:
            self.prev_fio = current
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
            self.current_readers_loaded += self.readers_page_size
            self.current_readers_loaded = min(self.current_readers_loaded, len(full))
            self.refresh()
        self.loading = False

    def get_filtered_students(self, full=False):
        cls_sel = self.class_filter.currentText()
        par_sel = self.parallel_filter.currentText()
        query = self.fio_search.text().lower()
        # Фильтрация по ФИО, классу, параллели
        students = []
        for s in self.app.students:
            if cls_sel != "Все" and s.get("class", "") != cls_sel:
                continue
            if par_sel != "Все" and s.get("parallel", "") != par_sel:
                continue
            if query and not (
                query in s.get("last_name", "").lower() or
                query in s.get("first_name", "").lower() or
                query in s.get("middle_name", "").lower()
            ):
                continue
            students.append(s)
        # Сортировка по алфавиту (фамилии)
        students.sort(key=lambda st: st.get("last_name", "").lower())
        mode = self.due_date_filter.currentText()
        today = QDate.currentDate()
        # Без сортировки и фильтров
        if mode == "Без сортировки и фильтров":
            result = students
        else:
            # Отбираем записи с любыми датами
            with_dates = []
            for s in students:
                if any(b.get("issue_date") or b.get("return_date") for b in s.get("books", [])):
                    with_dates.append(s)
            # Применяем режим
            if mode == "Сортировать по недавним выдачам":
                with_dates.sort(key=lambda st: max(
                    [QDate.fromString(b.get("issue_date", ""), "dd.MM.yyyy") for b in st.get("books", [])
                     if QDate.fromString(b.get("issue_date", ""), "dd.MM.yyyy").isValid()]
                    or [today]
                ), reverse=True)
            elif mode == "Сортировать по старым выдачам":
                with_dates.sort(key=lambda st: min(
                    [QDate.fromString(b.get("issue_date", ""), "dd.MM.yyyy") for b in st.get("books", [])
                     if QDate.fromString(b.get("issue_date", ""), "dd.MM.yyyy").isValid()]
                    or [today]
                ))
            elif mode == "Отобразить только просроченные сдачи":
                with_dates = [st for st in with_dates if any(
                    QDate.fromString(b.get("return_date", ""), "dd.MM.yyyy").isValid() and
                    QDate.fromString(b.get("return_date", ""), "dd.MM.yyyy") < today
                    for b in st.get("books", [])
                )]
            elif mode == "Отобразить только не просроченные сдачи":
                with_dates = [st for st in with_dates if any(
                    QDate.fromString(b.get("return_date", ""), "dd.MM.yyyy").isValid()
                    for b in st.get("books", [])
                ) and all(
                    not (QDate.fromString(b.get("return_date", ""), "dd.MM.yyyy").isValid() and
                         QDate.fromString(b.get("return_date", ""), "dd.MM.yyyy") < today)
                    for b in st.get("books", [])
                )]
            result = with_dates
        return result if full else result[:self.current_readers_loaded]

    def refresh(self):
        self.readers_table.clearSpans()
        self.refresh_filters()
        full = self.get_filtered_students(full=True)
        part = self.get_filtered_students(full=False)
        self.readers_table.setRowCount(0)
        for s in part:
            row = self.readers_table.rowCount()
            self.readers_table.insertRow(row)
            self.set_student_row(row, s)
        self.readers_status_label.setText(f"Читателей: {len(part)}/{len(full)}")

    def check_and_load_more(self):
        if self.current_readers_loaded < len(self.get_filtered_students(full=True)):
            self.load_more()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.check_and_load_more)

    def set_student_row(self, row, data):
        # Основные поля
        for i, key in enumerate(["last_name", "first_name", "middle_name", "class", "parallel"]):
            self.readers_table.setItem(row, i, QTableWidgetItem(data.get(key, "")))
        # Книги
        books = [b.get("book", "") for b in data.get("books", [])]
        self.readers_table.setItem(row, 5, QTableWidgetItem(
            ", ".join(books)
        ))
        # Даты и подсветка просрочек
        date_lines = []
        overdue = False
        today = QDate.currentDate()
        for b in data.get("books", []):
            issue = b.get("issue_date", "")
            ret = b.get("return_date", "")
            returned = b.get("returned", False)
            # Формируем текст для даты
            if issue and ret:
                date_lines.append(f"{issue} - {ret}")
            elif issue:
                date_lines.append(f"{issue} (выдана)")
            elif ret:
                date_lines.append(f"{ret} (сдача)")
            # Проверяем только невозвращенные книги
            if ret and not returned:
                rd = QDate.fromString(ret, "dd.MM.yyyy")
                if rd.isValid() and rd < today:
                    overdue = True
        if not date_lines:
            # Если нет дат, объединяем колонки Книги и Даты
            self.readers_table.setSpan(row, 5, 1, 2)
        item_date = QTableWidgetItem("\n".join(date_lines))
        self.readers_table.setItem(row, 6, item_date)
        # Подсветка строки, если есть просрочка среди невозвращенных
        if overdue:
            for col in range(self.readers_table.columnCount()):
                cell = self.readers_table.item(row, col)
                if cell:
                    cell.setBackground(QBrush(QColor('#ffa0a0')))

    def refresh_filters(self):
        cur_cls = self.class_filter.currentText()
        classes = ["Все"] + self.app.config.get("classes", [])
        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItems(classes)
        self.class_filter.setCurrentText(cur_cls if cur_cls in classes else "Все")
        self.class_filter.blockSignals(False)
        cur_par = self.parallel_filter.currentText()
        pars = ["Все"] + self.app.config.get("parallels", [])
        self.parallel_filter.blockSignals(True)
        self.parallel_filter.clear()
        self.parallel_filter.addItems(pars)
        self.parallel_filter.setCurrentText(cur_par if cur_par in pars else "Все")
        self.parallel_filter.blockSignals(False)
