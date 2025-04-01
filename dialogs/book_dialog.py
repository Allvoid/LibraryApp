from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtGui import QIntValidator

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
