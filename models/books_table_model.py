from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex

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

class BooksTableModel(QAbstractTableModel):
    def __init__(self, books=None):
        super().__init__()
        self._books = books or []
        self._headers = ["Название", "Автор", "Количество"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._books)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            book = self._books[index.row()]
            if index.column() == 0:
                return book.get("Title", "")
            elif index.column() == 1:
                return book.get("Author", "")
            elif index.column() == 2:
                quantity = book.get("quantity")
                return str(quantity) if quantity is not None else ""
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def updateBooks(self, books):
        self.beginResetModel()
        self._books = books
        self.endResetModel()
