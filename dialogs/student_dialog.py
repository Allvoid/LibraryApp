# dialogs/student_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSizePolicy,
    QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDateEdit,
    QScrollArea, QCompleter, QMessageBox, QStyle, QCheckBox
)
from PyQt6.QtCore import Qt, QDate

class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None, books_list=None, classes_list=None, parallels_list=None):
        super().__init__(parent)
        self.student_data = student_data or {}
        self.books_list = books_list or []
        self.classes_list = classes_list or []
        self.parallels_list = parallels_list or []
        self.book_selectors = []  # each tuple: (container, combo, option, issue_edit, return_edit, returned_cb)
        self.striked = bool(self.student_data.get('striked', False))
        self.setWindowTitle("Редактировать ученика" if student_data else "Добавить ученика")
        self._init_ui()
        self.resize(1100, 600)
        self.setMinimumSize(900, 600)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # ФИО
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        form_layout.addRow("Фамилия:", self.last_name_edit)
        form_layout.addRow("Имя:", self.first_name_edit)

        # Класс и параллель
        self.class_combo = QComboBox()
        self.class_combo.addItems(self.classes_list)
        form_layout.addRow("Класс:", self.class_combo)
        self.parallel_combo = QComboBox()
        self.parallel_combo.addItems(self.parallels_list)
        form_layout.addRow("Параллель:", self.parallel_combo)

        # Список книг
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

        # Заполнение при редактировании
        if self.student_data:
            self.last_name_edit.setText(self.student_data.get("last_name", ""))
            self.first_name_edit.setText(self.student_data.get("first_name", ""))
            self.class_combo.setCurrentText(self.student_data.get("class", ""))
            self.parallel_combo.setCurrentText(self.student_data.get("parallel", ""))
            for bk in self.student_data.get("books", []):
                issue = bk.get("issue_date", "")
                ret = bk.get("return_date", "")
                returned = bk.get("returned", False)
                option_text = (
                    "Указать дату выдачи и сдачи" if issue and ret else
                    "Указать дату выдачи" if issue else
                    "Указать дату сдачи" if ret else
                    "Не указывать даты"
                )
                initial_issue = QDate.fromString(issue, "dd.MM.yyyy") if issue else None
                initial_return = QDate.fromString(ret, "dd.MM.yyyy") if ret else None
                self.add_book_selector(
                    initial_text=bk.get("book", ""),
                    initial_option=option_text,
                    initial_issue=initial_issue,
                    initial_return=initial_return,
                    initial_returned=returned
                )
        else:
            self.add_book_selector()

        main_layout.addLayout(form_layout)

        # Кнопки
        btn_layout = QHBoxLayout()
        if self.student_data is not None:
            text = "Убрать выделение" if self.striked else "Вычеркнуть"
            self.strike_btn = QPushButton(text)
            self.strike_btn.clicked.connect(self.on_mark)
            btn_layout.addWidget(self.strike_btn)

            delete_btn = QPushButton("Удалить ученика")
            delete_btn.clicked.connect(self.on_delete_clicked)
            btn_layout.addWidget(delete_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить ученика")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def on_mark(self):
        self.striked = not self.striked
        self.strike_btn.setText("Убрать выделение" if self.striked else "Вычеркнуть")
        self.done(3)

    def on_delete_clicked(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Подтверждение")
        msg.setText("Вы уверены, что хотите удалить ученика?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        yes = msg.button(QMessageBox.StandardButton.Yes)
        no = msg.button(QMessageBox.StandardButton.No)
        yes.setText("Да")
        no.setText("Нет")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.done(2)

    def add_book_selector(self, initial_text="", initial_option="Не указывать даты",
                          initial_issue=None, initial_return=None, initial_returned=False, initial_returned_date=None):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        combo = QComboBox(); combo.setEditable(True)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.addItems(self.books_list)
        combo.setCurrentText(initial_text)
        if combo.lineEdit(): combo.lineEdit().setPlaceholderText("Выберите книгу или введите новую")
        combo.setCompleter(QCompleter(self.books_list))
        h_layout.addWidget(combo)

        option = QComboBox(); option.addItems([
            "Не указывать даты", "Указать дату выдачи", "Указать дату сдачи", "Указать дату выдачи и сдачи"
        ])
        option.setCurrentText(initial_option)
        h_layout.addWidget(option)

        issue_edit = QDateEdit(); issue_edit.setCalendarPopup(True); issue_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_issue and initial_issue.isValid(): issue_edit.setDate(initial_issue)
        else: issue_edit.setDate(QDate.currentDate())
        h_layout.addWidget(issue_edit)

        dash = QLabel("-"); h_layout.addWidget(dash)

        return_edit = QDateEdit(); return_edit.setCalendarPopup(True); return_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_return and initial_return.isValid(): return_edit.setDate(initial_return)
        else: return_edit.setDate(QDate.currentDate())
        h_layout.addWidget(return_edit)

        # Checkbox returned
        returned_cb = QCheckBox("Сдана")
        returned_cb.setChecked(initial_returned or bool(initial_return))
        h_layout.addWidget(returned_cb)

        # If returned, show returned date selector
        returned_date_label = QLabel("была сдана в")
        returned_date_edit = QDateEdit(); returned_date_edit.setCalendarPopup(True); returned_date_edit.setDisplayFormat("dd.MM.yyyy")
        if initial_returned_date and initial_returned_date.isValid():
            returned_date_edit.setDate(initial_returned_date)
        else:
            returned_date_edit.setDate(QDate.currentDate())
        returned_date_label.setVisible(returned_cb.isChecked())
        returned_date_edit.setVisible(returned_cb.isChecked())
        h_layout.addWidget(returned_date_label)
        h_layout.addWidget(returned_date_edit)

        # Toggle returned date visibility
        def on_returned_toggled(checked):
            returned_date_label.setVisible(checked)
            returned_date_edit.setVisible(checked)
        returned_cb.toggled.connect(on_returned_toggled)

        delete_btn = QPushButton(); delete_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); delete_btn.setFlat(True)
        h_layout.addWidget(delete_btn)

        def update_fields(opt):
            show_i = opt in ["Указать дату выдачи", "Указать дату выдачи и сдачи"]
            show_r = opt in ["Указать дату сдачи", "Указать дату выдачи и сдачи"]
            issue_edit.setVisible(show_i)
            return_edit.setVisible(show_r)
            dash.setVisible(show_i and show_r)
        option.currentTextChanged.connect(update_fields)
        update_fields(initial_option)

        self.books_layout.addWidget(container)
        self.book_selectors.append((container, combo, option, issue_edit, return_edit, returned_cb, returned_date_edit))
        delete_btn.clicked.connect(lambda: self.remove_book_selector(container))
        self.update_delete_buttons()

    def remove_book_selector(self, container):
        for i, tpl in enumerate(self.book_selectors):
            if tpl[0] is container:
                widget, *_ = self.book_selectors.pop(i)
                widget.setParent(None)
                widget.deleteLater()
                break
        self.update_delete_buttons()

    def update_delete_buttons(self):
        count = len(self.book_selectors)
        for tpl in self.book_selectors:
            btn = tpl[0].findChild(QPushButton)
            btn.setEnabled(count > 1)

    def get_data(self):
        books = []
        for container, combo, option, issue_edit, return_edit, returned_cb, returned_date_edit in self.book_selectors:
            text = combo.currentText().strip()
            if not text:
                continue
            opt = option.currentText()
            issue = issue_edit.date().toString("dd.MM.yyyy") if opt in ["Указать дату выдачи", "Указать дату выдачи и сдачи"] else ""
            ret = return_edit.date().toString("dd.MM.yyyy") if opt in ["Указать дату сдачи", "Указать дату выдачи и сдачи"] else ""
            returned = returned_cb.isChecked()
            returned_date = returned_date_edit.date().toString("dd.MM.yyyy") if returned else ""
            books.append({
                "book": text,
                "issue_date": issue,
                "return_date": ret,
                "returned": returned,
                "returned_date": returned_date
            })
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
