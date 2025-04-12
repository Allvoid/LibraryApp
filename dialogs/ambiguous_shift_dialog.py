# dialogs/ambiguous_shift_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

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

class AmbiguousShiftDialog(QDialog):
    def __init__(self, ambiguous_students, last_class, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор для неоднозначных учеников")
        self.ambiguous_students = ambiguous_students  # список учеников (словарей)
        self.last_class = last_class
        self.decisions = {}  # для каждой строки: "shift" или "delete"
        self.row_widgets = []  # список кортежей (shift_btn, delete_btn) для каждой строки
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("Для следующих учеников выбор неоднозначен. Выберите действие для каждого:")
        layout.addWidget(info_label)

        self.table = QTableWidget(len(self.ambiguous_students), 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Класс", "Перевести", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.row_widgets = []
        for row, st in enumerate(self.ambiguous_students):
            fio = f'{st.get("last_name", "")} {st.get("first_name", "")} {st.get("middle_name", "")}'
            self.table.setItem(row, 0, QTableWidgetItem(fio))
            self.table.setItem(row, 1, QTableWidgetItem(st.get("class", "")))
            btn_shift = QPushButton("Перевести")
            btn_delete = QPushButton("Удалить")
            # Если ученик из последнего класса, кнопка "Перевести" отключается
            if st.get("class", "") == self.last_class:
                btn_shift.setEnabled(False)
            btn_shift.clicked.connect(lambda checked, r=row: self.set_decision(r, "shift"))
            btn_delete.clicked.connect(lambda checked, r=row: self.on_delete_clicked(r))
            self.table.setCellWidget(row, 2, btn_shift)
            self.table.setCellWidget(row, 3, btn_delete)
            self.row_widgets.append((btn_shift, btn_delete))
        layout.addWidget(self.table)

        # Дополнительные кнопки для массового выбора
        btn_layout = QHBoxLayout()
        self.select_all_delete_btn = QPushButton("Выбрать всех для удаления")
        self.select_all_delete_btn.clicked.connect(self.select_all_delete)
        self.select_all_shift_btn = QPushButton("Выбрать всех для перевода")
        self.select_all_shift_btn.clicked.connect(self.select_all_shift)
        btn_layout.addWidget(self.select_all_delete_btn)
        btn_layout.addWidget(self.select_all_shift_btn)
        layout.addLayout(btn_layout)

        # Кнопки "Применить" и "Отмена"
        action_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(self.on_apply)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        action_layout.addStretch()
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.apply_btn)
        layout.addLayout(action_layout)

        self.check_all_decisions_set()

    def set_decision(self, row, decision):
        self.decisions[row] = decision
        # Обновляем стили для кнопок в строке row
        shift_btn, delete_btn = self.row_widgets[row]
        if decision == "shift":
            shift_btn.setStyleSheet("background-color: lightgreen;")
            delete_btn.setStyleSheet("")
        elif decision == "delete":
            delete_btn.setStyleSheet("background-color: red; color: white;")
            shift_btn.setStyleSheet("")
        self.check_all_decisions_set()

    def on_delete_clicked(self, row):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы уверены, что хотите удалить этого ученика?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        no_button = msg_box.button(QMessageBox.StandardButton.No)
        yes_button.setText("Да")
        no_button.setText("Нет")
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Yes.value:
            self.set_decision(row, "delete")

    def select_all_delete(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы действительно хотите выбрать всех для удаления?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        no_button = msg_box.button(QMessageBox.StandardButton.No)
        yes_button.setText("Да")
        no_button.setText("Нет")
        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Yes.value:
            for row in range(len(self.ambiguous_students)):
                self.decisions[row] = "delete"
                shift_btn, delete_btn = self.row_widgets[row]
                delete_btn.setStyleSheet("background-color: red; color: white;")
                shift_btn.setStyleSheet("")
            self.check_all_decisions_set()

    def select_all_shift(self):
        for row in range(len(self.ambiguous_students)):
            # Если ученик из последнего класса, кнопка "Перевести" остается отключенной
            if self.ambiguous_students[row].get("class", "") == self.last_class:
                continue
            self.decisions[row] = "shift"
            shift_btn, delete_btn = self.row_widgets[row]
            shift_btn.setStyleSheet("background-color: lightgreen;")
            delete_btn.setStyleSheet("")
        self.check_all_decisions_set()

    def check_all_decisions_set(self):
        self.apply_btn.setEnabled(len(self.decisions) == len(self.ambiguous_students))

    def on_apply(self):
        for row, st in enumerate(self.ambiguous_students):
            decision = self.decisions.get(row)
            if decision == "shift":
                if st.get("class", "").isdigit():
                    st["class"] = str(int(st["class"]) + 1)
            elif decision == "delete":
                st["to_delete"] = True
        self.accept()
