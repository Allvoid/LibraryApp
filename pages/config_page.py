# pages/config_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QLineEdit, QPushButton, QLabel

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

class ConfigPage(QWidget):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._init_ui()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        main_layout = QHBoxLayout()
        # Группа классов
        classes_group = QGroupBox("Классы")
        classes_layout = QVBoxLayout(classes_group)
        self.classes_list_widget = QListWidget()
        self.classes_list_widget.addItems(self.app.config.get("classes", []))
        classes_layout.addWidget(self.classes_list_widget)
        add_class_layout = QHBoxLayout()
        self.new_class_edit = QLineEdit()
        self.new_class_edit.setPlaceholderText("Новый класс")
        add_class_btn = QPushButton("Добавить")
        add_class_btn.clicked.connect(self.app.add_class)
        add_class_layout.addWidget(self.new_class_edit)
        add_class_layout.addWidget(add_class_btn)
        classes_layout.addLayout(add_class_layout)
        del_class_btn = QPushButton("Удалить выбранное")
        del_class_btn.clicked.connect(self.app.delete_class)
        classes_layout.addWidget(del_class_btn)
        classes_layout.addStretch()
        main_layout.addWidget(classes_group)
        # Группа параллелей
        parallels_group = QGroupBox("Параллели")
        parallels_layout = QVBoxLayout(parallels_group)
        self.parallels_list_widget = QListWidget()
        self.parallels_list_widget.addItems(self.app.config.get("parallels", []))
        parallels_layout.addWidget(self.parallels_list_widget)
        add_parallel_layout = QHBoxLayout()
        self.new_parallel_edit = QLineEdit()
        self.new_parallel_edit.setPlaceholderText("Новая параллель")
        add_parallel_btn = QPushButton("Добавить")
        add_parallel_btn.clicked.connect(self.app.add_parallel)
        add_parallel_layout.addWidget(self.new_parallel_edit)
        add_parallel_layout.addWidget(add_parallel_btn)
        parallels_layout.addLayout(add_parallel_layout)
        del_parallel_btn = QPushButton("Удалить выбранное")
        del_parallel_btn.clicked.connect(self.app.delete_parallel)
        parallels_layout.addWidget(del_parallel_btn)
        parallels_layout.addStretch()
        main_layout.addWidget(parallels_group)
        outer_layout.addLayout(main_layout)
        # Нижняя панель: убираем кнопку "Сохранить изменения", оставляем только кнопку сдвига учеников
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        shift_btn = QPushButton("Сдвинуть учеников на следующий класс")
        shift_btn.clicked.connect(self.app.shift_students)
        bottom_layout.addWidget(shift_btn)
        bottom_layout.addStretch()
        outer_layout.addLayout(bottom_layout)

    def refresh(self):
        self.classes_list_widget.clear()
        self.classes_list_widget.addItems(self.app.config.get("classes", []))
        self.parallels_list_widget.clear()
        self.parallels_list_widget.addItems(self.app.config.get("parallels", []))
