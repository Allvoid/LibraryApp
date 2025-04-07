from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex

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
