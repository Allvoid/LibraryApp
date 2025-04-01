from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QCompleter, QSizePolicy,
    QPushButton, QWidget, QHBoxLayout, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtWidgets import QStyle

class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None, books_list=None, classes_list=None, parallels_list=None):
        super().__init__(parent)
        self.student_data = student_data
        self.books_list = books_list if books_list is not None else []
        self.classes_list = classes_list if classes_list is not None else []
        self.parallels_list = parallels_list if parallels_list is not None else []
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
        self.books_widget = QWidget()
        self.books_layout = QHBoxLayout(self.books_widget)
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
                    if isinstance(bk, dict):
                        initial_text = bk.get("book", "")
                        initial_date = QDate.fromString(bk.get("due_date", ""), "dd.MM.yyyy")
                        self.add_book_selector(initial_text=initial_text, initial_date=initial_date)
                    else:
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

    def add_book_selector(self, initial_text="", initial_date=None):
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
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_date and initial_date.isValid():
            date_edit.setDate(initial_date)
        else:
            date_edit.setDate(QDate.currentDate())
        h_layout.addWidget(date_edit)
        delete_btn = QPushButton()
        trash_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        delete_btn.setIcon(trash_icon)
        delete_btn.setMaximumSize(24, 24)
        delete_btn.setFlat(True)
        h_layout.addWidget(delete_btn)
        self.book_selectors.append((container, combo, date_edit, delete_btn))
        self.books_layout.addWidget(container)
        delete_btn.clicked.connect(lambda: QTimer.singleShot(0, lambda: self.remove_book_selector(container)))
        self.update_delete_buttons()

    def remove_book_selector(self, container):
        for i, (cont, combo, date_edit, delete_btn) in enumerate(self.book_selectors):
            if cont is container:
                self.book_selectors.pop(i)
                container.setParent(None)
                container.deleteLater()
                break
        self.update_delete_buttons()

    def update_delete_buttons(self):
        count = len(self.book_selectors)
        for (container, combo, date_edit, delete_btn) in self.book_selectors:
            delete_btn.setEnabled(False if count == 1 else True)

    def get_data(self):
        books = []
        for (_, combo, date_edit, _) in self.book_selectors:
            book_text = combo.currentText().strip()
            if book_text:
                due_date = date_edit.date().toString("dd.MM.yyyy")
                books.append({"book": book_text, "due_date": due_date})
        return {
            "last_name": self.last_name_edit.text().strip(),
            "first_name": self.first_name_edit.text().strip(),
            "middle_name": self.middle_name_edit.text().strip(),
            "class": self.class_combo.currentText(),
            "parallel": self.parallel_combo.currentText(),
            "books": books
        }
