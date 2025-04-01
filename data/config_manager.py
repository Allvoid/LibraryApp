import os
import json
from os.path import dirname, abspath, join
BASE_DIR = dirname(dirname(abspath(__file__)))
config_path = join(BASE_DIR, "config.json")

def load_config():
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Ошибка загрузки config.json:", e)
    return {
        "classes": [str(i) for i in range(1, 12)],
        "parallels": ["А", "Б", "В", "Г", "Д", "Л", "М"]
    }

def save_config(config):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Ошибка сохранения config.json:", e)
