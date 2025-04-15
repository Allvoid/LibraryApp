# dialogs/student_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QCompleter, QSizePolicy,
    QPushButton, QWidget, QHBoxLayout, QDateEdit, QVBoxLayout, QStyle,
    QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QDate

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
        self.books_list = books_list if books_list is not None else []
        self.classes_list = classes_list if classes_list is not None else []
        self.parallels_list = parallels_list if parallels_list is not None else []
        self.book_selectors = []
        self.setWindowTitle("Редактировать ученика" if student_data else "Добавить ученика")
        self._init_ui()
        # Устанавливаем увеличенный размер окна по умолчанию
        self.resize(700, 400)

    def _init_ui(self):
        # Создаем главный вертикальный layout для всего диалога
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Создаем форму через QFormLayout для остальных элементов
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # -------------------- Поля ФИО --------------------
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.middle_name_edit = QLineEdit()
        self.middle_name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form_layout.addRow("Фамилия:", self.last_name_edit)
        form_layout.addRow("Имя:", self.first_name_edit)
        # Изменили метку для отчества, чтобы указать, что поле необязательно
        form_layout.addRow("Отчество (Необязательно):", self.middle_name_edit)

        # -------------------- Класс и Параллель --------------------
        self.class_combo = QComboBox()
        self.class_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.class_combo.addItems(self.classes_list)
        form_layout.addRow("Класс:", self.class_combo)

        self.parallel_combo = QComboBox()
        self.parallel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.parallel_combo.addItems(self.parallels_list)
        form_layout.addRow("Параллель:", self.parallel_combo)

        # -------------------- Список книг (прокрутка) --------------------
        self.books_widget = QWidget()
        self.books_layout = QVBoxLayout(self.books_widget)
        self.books_layout.setContentsMargins(0, 0, 0, 0)
        self.books_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.books_scroll_area = QScrollArea()
        self.books_scroll_area.setWidgetResizable(True)
        self.books_scroll_area.setWidget(self.books_widget)
        self.books_scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        form_layout.addRow("Книги:", self.books_scroll_area)

        add_book_btn = QPushButton("Добавить книгу")
        add_book_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_book_btn.clicked.connect(lambda: self.add_book_selector())
        form_layout.addRow(add_book_btn)

        # -------------------- Заполнение данными при редактировании --------------------
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
                        due_date_str = bk.get("due_date", "")
                        initial_date = QDate.fromString(due_date_str, "dd.MM.yyyy") if due_date_str else None
                        self.add_book_selector(initial_text=initial_text, initial_date=initial_date)
                    else:
                        self.add_book_selector(initial_text=bk)
            else:
                self.add_book_selector()
        else:
            self.add_book_selector()

        main_layout.addLayout(form_layout)

        # -------------------- Кнопки управления --------------------
        btn_layout = QHBoxLayout()
        if self.student_data is not None:
            delete_btn = QPushButton("Удалить ученика")
            delete_btn.clicked.connect(lambda: self.done(2))
            btn_layout.addWidget(delete_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("Сохранить ученика")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def add_book_selector(self, initial_text="", initial_date=None):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        combo = QComboBox()
        combo.setEditable(True)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.addItems(self.books_list)
        completer = QCompleter(self.books_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.setCompleter(completer)
        combo.setCurrentText(initial_text)
        h_layout.addWidget(combo)

        check_due = QCheckBox("Указать срок сдачи")
        if initial_date and initial_date.isValid():
            check_due.setChecked(True)
        else:
            check_due.setChecked(False)
        h_layout.addWidget(check_due)

        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_date and initial_date.isValid():
            date_edit.setDate(initial_date)
            date_edit.setVisible(True)
        else:
            date_edit.setDate(QDate.currentDate())
            date_edit.setVisible(False)
        h_layout.addWidget(date_edit)

        check_due.stateChanged.connect(lambda state: date_edit.setVisible(state == Qt.CheckState.Checked.value))

        delete_btn = QPushButton()
        trash_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        delete_btn.setIcon(trash_icon)
        delete_btn.setMaximumSize(24, 24)
        delete_btn.setFlat(True)
        h_layout.addWidget(delete_btn)

        self.book_selectors.append((container, combo, check_due, date_edit, delete_btn))
        self.books_layout.addWidget(container)
        delete_btn.clicked.connect(lambda: QTimer.singleShot(0, lambda: self.remove_book_selector(container)))
        self.update_delete_buttons()

    def remove_book_selector(self, container):
        for i, (cont, combo, check_due, date_edit, delete_btn) in enumerate(self.book_selectors):
            if cont is container:
                self.book_selectors.pop(i)
                container.setParent(None)
                container.deleteLater()
                break
        self.update_delete_buttons()

    def update_delete_buttons(self):
        count = len(self.book_selectors)
        for (container, combo, check_due, date_edit, delete_btn) in self.book_selectors:
            delete_btn.setEnabled(count > 1)

    def get_data(self):
        books = []
        for (_, combo, check_due, date_edit, _) in self.book_selectors:
            book_text = combo.currentText().strip()
            if book_text:
                if check_due.isChecked():
                    due_date = date_edit.date().toString("dd.MM.yyyy")
                else:
                    due_date = ""
                books.append({"book": book_text, "due_date": due_date})
        return {
            "last_name": self.last_name_edit.text().strip(),
            "first_name": self.first_name_edit.text().strip(),
            "middle_name": self.middle_name_edit.text().strip(),
            "class": self.class_combo.currentText(),
            "parallel": self.parallel_combo.currentText(),
            "books": books
        }

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dlg = StudentDialog()
    if dlg.exec() == QDialog.DialogCode.Accepted:
        print(dlg.get_data())
