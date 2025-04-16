# pages/books_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableView,
    QPushButton, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import QTimer, QEvent
from PyQt6.QtGui import QResizeEvent
from models.books_table_model import BooksTableModel

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

class BooksPage(QWidget):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.books_page_size = 50
        self.current_books_loaded = 0
        self.prev_query = ""
        self.loading = False
        self._init_ui()
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.check_and_load_more)
        self.auto_timer.start(500)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Поисковая панель
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.book_search_edit = QLineEdit()
        self.book_search_edit.setPlaceholderText("Искать по названию или автору...")
        self.book_search_edit.textChanged.connect(self.on_book_search_text_changed)
        search_layout.addWidget(self.book_search_edit)
        layout.addLayout(search_layout)

        # Таблица книг
        self.books_table_view = QTableView()
        self.books_model = BooksTableModel([])
        self.books_table_view.setModel(self.books_model)
        self.books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.books_table_view.verticalHeader().setVisible(True)

        # Отключаем редактирование, выделяем строку
        self.books_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.books_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.books_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        layout.addWidget(self.books_table_view)

        # Сброс выделения по клику в пустом месте
        self.books_table_view.viewport().installEventFilter(self)
        self.installEventFilter(self)

        # Кнопки
        btn_layout = QHBoxLayout()
        add_book_btn = QPushButton("Добавить книгу")
        add_book_btn.clicked.connect(self.app.add_book)
        del_book_btn = QPushButton("Удалить книгу")
        del_book_btn.clicked.connect(self.app.delete_book)
        clear_books_btn = QPushButton("Очистить все книги")
        clear_books_btn.clicked.connect(self.app.clear_all_books)
        btn_layout.addWidget(add_book_btn)
        btn_layout.addWidget(del_book_btn)
        btn_layout.addWidget(clear_books_btn)
        layout.addLayout(btn_layout)

        # Статус
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.books_status_label = QLabel("Книг: 0/0")
        status_layout.addWidget(self.books_status_label)
        layout.addLayout(status_layout)

        # Автозагрузка при скролле
        self.books_table_view.verticalScrollBar().valueChanged.connect(self.on_books_scroll)

        # Инициализация
        self.prev_query = self.book_search_edit.text().lower()
        self.current_books_loaded = self.books_page_size
        self.refresh()

    def mousePressEvent(self, event):
        # При клике вне таблицы сброс выделения
        if not self.books_table_view.geometry().contains(event.pos()):
            self.books_table_view.clearSelection()
        super().mousePressEvent(event)

    def eventFilter(self, source, event):
        if source == self.books_table_view.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            if not self.books_table_view.indexAt(event.pos()).isValid():
                self.books_table_view.clearSelection()
        return super().eventFilter(source, event)

    def on_book_search_text_changed(self):
        current = self.book_search_edit.text().lower()
        if current != self.prev_query:
            self.prev_query = current
            self.current_books_loaded = self.books_page_size
        self.refresh()

    def on_books_scroll(self, value):
        if value == self.books_table_view.verticalScrollBar().maximum():
            self.load_more()

    def load_more(self):
        if self.loading:
            return
        self.loading = True
        all_books = self._filtered_books()
        if self.current_books_loaded < len(all_books):
            self.current_books_loaded = min(len(all_books), self.current_books_loaded + self.books_page_size)
            self.refresh()
        self.loading = False

    def _filtered_books(self):
        query = self.book_search_edit.text().lower()
        return [
            bk for bk in self.app.books
            if not query
            or query in bk.get("Title", "").lower()
            or query in bk.get("Author", "").lower()
        ]

    def refresh(self):
        all_books = self._filtered_books()
        display = all_books[:self.current_books_loaded]
        self.books_model.updateBooks(display)
        self.books_status_label.setText(f"Книг: {len(display)}/{len(all_books)}")

    def check_and_load_more(self):
        if self.current_books_loaded < len(self._filtered_books()):
            self.load_more()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.check_and_load_more)
