from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt

class AmbiguousShiftDialog(QDialog):
    def __init__(self, ambiguous_students, last_class, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор для неоднозначных учеников")
        self.ambiguous_students = ambiguous_students
        self.last_class = last_class
        self.decisions = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("Для следующих учеников выбор неоднозначен. Выберите действие для каждого:")
        layout.addWidget(info_label)
        self.table = QTableWidget(len(self.ambiguous_students), 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Класс", "Перевести", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row, st in enumerate(self.ambiguous_students):
            fio = f'{st.get("last_name", "")} {st.get("first_name", "")} {st.get("middle_name", "")}'
            self.table.setItem(row, 0, QTableWidgetItem(fio))
            self.table.setItem(row, 1, QTableWidgetItem(st.get("class", "")))
            btn_shift = QPushButton("Перевести")
            btn_delete = QPushButton("Удалить")
            btn_shift.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_delete.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if st.get("class", "") == self.last_class:
                btn_shift.setEnabled(False)
            btn_shift.clicked.connect(lambda checked, r=row: self.set_decision(r, "shift"))
            btn_delete.clicked.connect(lambda checked, r=row: self.on_delete_clicked(r))
            self.table.setCellWidget(row, 2, btn_shift)
            self.table.setCellWidget(row, 3, btn_delete)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(self.on_apply)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        self.check_all_decisions_set()

    def set_decision(self, row, decision):
        self.decisions[row] = decision
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(Qt.GlobalColor.lightGray)
        self.check_all_decisions_set()

    def on_delete_clicked(self, row):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Подтверждение удаления")
        msgBox.setText("Вы уверены, ведь удалиться и долг ученика?")
        yesButton = msgBox.addButton("Да", QMessageBox.ButtonRole.YesRole)
        noButton = msgBox.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        msgBox.exec()
        if msgBox.clickedButton() == yesButton:
            self.set_decision(row, "delete")

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
