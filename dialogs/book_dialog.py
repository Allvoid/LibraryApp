# dialogs/book_dialog.py
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtGui import QIntValidator

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

class BookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить книгу")
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.title_edit = QLineEdit()
        self.title_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.author_edit = QLineEdit()
        self.author_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(1, 1000000, self))
        layout.addRow("Название:", self.title_edit)
        layout.addRow("Автор:", self.author_edit)
        layout.addRow("Количество (необязательно):", self.quantity_edit)
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить книгу")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        quantity_text = self.quantity_edit.text().strip()
        quantity = int(quantity_text) if quantity_text else None
        return {
            "Title": self.title_edit.text().strip(),
            "Author": self.author_edit.text().strip(),
            "quantity": quantity
        }
