import os
import re
from os.path import dirname, abspath, join
BASE_DIR = dirname(dirname(abspath(__file__)))
books_path = join(BASE_DIR, "литература.txt")

def load_books():
    books = []
    if os.path.exists(books_path):
        try:
            with open(books_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().rstrip(',')
                    m = re.search(r'\{Title\s*=\s*"([^"]+)"\s*,\s*Author\s*=\s*"([^"]+)"(?:\s*,\s*Quantity\s*=\s*"([^"]*)")?\}', line)
                    if m:
                        title = m.group(1)
                        author = m.group(2)
                        quantity_str = m.group(3)
                        quantity = int(quantity_str) if quantity_str and quantity_str.isdigit() else None
                        books.append({"Title": title, "Author": author, "quantity": quantity})
        except Exception as e:
            print("Ошибка загрузки литература.txt:", e)
    return books

def save_books(books):
    try:
        with open(books_path, "w", encoding="utf-8") as f:
            for book in books:
                quantity = book.get("quantity")
                q_str = f'", Quantity = "{quantity}"' if quantity is not None else ""
                line = f'{{Title = "{book.get("Title", "")}", Author = "{book.get("Author", "")}"{q_str}}},\n'
                f.write(line)
    except Exception as e:
        print("Ошибка сохранения литература.txt:", e)
