# dialogs/student_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSizePolicy,
    QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDateEdit,
    QScrollArea, QCompleter, QMessageBox, QStyle
)
from PyQt6.QtCore import Qt, QDate

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

class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None, books_list=None, classes_list=None, parallels_list=None):
        super().__init__(parent)
        self.student_data = student_data
        self.books_list = books_list or []
        self.classes_list = classes_list or []
        self.parallels_list = parallels_list or []
        self.book_selectors = []
        self.setWindowTitle("Редактировать ученика" if student_data else "Добавить ученика")
        self._init_ui()
        # Зафиксированный размер диалога
        self.resize(1100, 600)
        self.setMinimumSize(900, 600)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # --- ФИО ---
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        form_layout.addRow("Фамилия:", self.last_name_edit)
        form_layout.addRow("Имя:", self.first_name_edit)

        # --- Класс и параллель ---
        self.class_combo = QComboBox()
        self.class_combo.addItems(self.classes_list)
        form_layout.addRow("Класс:", self.class_combo)
        self.parallel_combo = QComboBox()
        self.parallel_combo.addItems(self.parallels_list)
        form_layout.addRow("Параллель:", self.parallel_combo)

        # --- Список книг ---
        self.books_widget = QWidget()
        self.books_layout = QVBoxLayout(self.books_widget)
        self.books_layout.setContentsMargins(0, 0, 0, 0)
        self.books_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.books_scroll_area = QScrollArea()
        self.books_scroll_area.setWidgetResizable(True)
        self.books_scroll_area.setWidget(self.books_widget)
        form_layout.addRow("Книги:", self.books_scroll_area)

        add_book_btn = QPushButton("Добавить книгу")
        add_book_btn.clicked.connect(lambda: self.add_book_selector())
        form_layout.addRow(add_book_btn)

        # --- Заполнение при редактировании ---
        if self.student_data:
            self.last_name_edit.setText(self.student_data.get("last_name", ""))
            self.first_name_edit.setText(self.student_data.get("first_name", ""))
            self.class_combo.setCurrentText(self.student_data.get("class", ""))
            self.parallel_combo.setCurrentText(self.student_data.get("parallel", ""))
            for bk in self.student_data.get("books", []):
                issue = bk.get("issue_date", "")
                ret = bk.get("return_date", "")
                option_text = (
                    "Указать дату выдачи и сдачи" if issue and ret else
                    "Указать дату выдачи" if issue else
                    "Указать дату сдачи" if ret else
                    "Не указывать даты"
                )
                issue_date = QDate.fromString(issue, "dd.MM.yyyy") if issue else None
                return_date = QDate.fromString(ret, "dd.MM.yyyy") if ret else None
                self.add_book_selector(
                    initial_text=bk.get("book", ""),
                    initial_option=option_text,
                    initial_issue=issue_date,
                    initial_return=return_date
                )
        else:
            self.add_book_selector()

        main_layout.addLayout(form_layout)

        # --- Кнопки ---
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
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def add_book_selector(self, initial_text="", initial_option="Не указывать даты",
                          initial_issue=None, initial_return=None):
        """
        Добавляет селектор для книги с возможностью ввода новой записи.
        """
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # Комбобокс (книги) с вводом нового
        combo = QComboBox()
        combo.setEditable(True)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.addItems(self.books_list)
        if initial_text:
            combo.setCurrentText(initial_text)
        else:
            combo.setCurrentText("")
        if combo.lineEdit():
            combo.lineEdit().setPlaceholderText("Выберите книгу или введите новую")
        completer = QCompleter(self.books_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.setCompleter(completer)
        h_layout.addWidget(combo)

        # Опции дат
        option = QComboBox()
        option.addItems([
            "Не указывать даты",
            "Указать дату выдачи",
            "Указать дату сдачи",
            "Указать дату выдачи и сдачи"
        ])
        option.setCurrentText(initial_option)
        h_layout.addWidget(option)

        # Дата выдачи
        issue_edit = QDateEdit()
        issue_edit.setCalendarPopup(True)
        issue_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_issue and initial_issue.isValid():
            issue_edit.setDate(initial_issue)
        else:
            issue_edit.setDate(QDate.currentDate())
        h_layout.addWidget(issue_edit)

        # Разделитель
        dash = QLabel("-")
        h_layout.addWidget(dash)

        # Дата сдачи
        return_edit = QDateEdit()
        return_edit.setCalendarPopup(True)
        return_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_return and initial_return.isValid():
            return_edit.setDate(initial_return)
        else:
            return_edit.setDate(QDate.currentDate())
        h_layout.addWidget(return_edit)

        # Кнопка удаления селектора
        delete_btn = QPushButton()
        delete_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        delete_btn.setFlat(True)
        h_layout.addWidget(delete_btn)

        # Видимость полей дат
        def update_fields(opt_text):
            show_i = opt_text in ["Указать дату выдачи", "Указать дату выдачи и сдачи"]
            show_r = opt_text in ["Указать дату сдачи", "Указать дату выдачи и сдачи"]
            issue_edit.setVisible(show_i)
            return_edit.setVisible(show_r)
            dash.setVisible(show_i and show_r)
        option.currentTextChanged.connect(update_fields)
        update_fields(initial_option)

        # Добавление селектора
        self.book_selectors.append((container, combo, option, issue_edit, return_edit))
        self.books_layout.addWidget(container)
        delete_btn.clicked.connect(lambda: self.remove_book_selector(container))
        self.update_delete_buttons()

    def remove_book_selector(self, container):
        for i, (cont, combo, opt, ie, re) in enumerate(self.book_selectors):
            if cont is container:
                self.book_selectors.pop(i)
                cont.setParent(None)
                cont.deleteLater()
                break
        self.update_delete_buttons()

    def update_delete_buttons(self):
        count = len(self.book_selectors)
        for cont, combo, opt, ie, re in self.book_selectors:
            btn = cont.findChild(QPushButton)
            btn.setEnabled(count > 1)

    def get_data(self):
        books = []
        for container, combo, option, issue_edit, return_edit in self.book_selectors:
            text = combo.currentText().strip()
            if not text:
                continue
            opt = option.currentText()
            issue = issue_edit.date().toString("dd.MM.yyyy") if opt in ["Указать дату выдачи", "Указать дату выдачи и сдачи"] else ""
            ret = return_edit.date().toString("dd.MM.yyyy") if opt in ["Указать дату сдачи", "Указать дату выдачи и сдачи"] else ""
            books.append({"book": text, "issue_date": issue, "return_date": ret})
        return {
            "last_name": self.last_name_edit.text().strip(),
            "first_name": self.first_name_edit.text().strip(),
            "class": self.class_combo.currentText(),
            "parallel": self.parallel_combo.currentText(),
            "books": books
        }

    def accept(self):
        data = self.get_data()
        if not data.get("books"):
            QMessageBox.warning(self, "Ошибка", "Не выбрана книга!\nПожалуйста, добавьте и выберите книгу.")
            return
        super().accept()
