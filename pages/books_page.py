from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QHeaderView
from models.books_table_model import BooksTableModel

class BooksPage(QWidget):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        # Панель поиска
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.book_search_edit = QLineEdit()
        self.book_search_edit.setPlaceholderText("Искать по названию или автору...")
        self.book_search_edit.textChanged.connect(self.on_book_search_text_changed)
        search_layout.addWidget(self.book_search_edit)
        layout.addLayout(search_layout)
        # QTableView с моделью для книг
        self.books_table_view = QTableView()
        self.books_model = BooksTableModel(self.app.books)
        self.books_table_view.setModel(self.books_model)
        self.books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.books_table_view.verticalHeader().setVisible(True)
        # Настройка выбора всей строки
        self.books_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.books_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        layout.addWidget(self.books_table_view)
        # Панель кнопок
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
        self.refresh()

    def on_book_search_text_changed(self):
        self.refresh()

    def refresh(self):
        query = self.book_search_edit.text().lower()
        filtered = [bk for bk in self.app.books if (not query) or
                    (query in bk.get("Title", "").lower() or query in bk.get("Author", "").lower())]
        self.books_model.updateBooks(filtered)
        total = len(filtered)
        self.books_status_label.setText(f"Книг: {total}/{len(self.app.books)}")
