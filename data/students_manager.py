import os
import json
from os.path import dirname, abspath, join
BASE_DIR = dirname(dirname(abspath(__file__)))
students_path = join(BASE_DIR, "students.json")

def load_students():
    if os.path.exists(students_path):
        try:
            with open(students_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Ошибка загрузки students.json:", e)
    return []

def save_students(students):
    try:
        with open(students_path, "w", encoding="utf-8") as f:
            json.dump(students, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Ошибка сохранения students.json:", e)
