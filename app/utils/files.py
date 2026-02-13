#app/utils/files.py
import json
import os

def get_base_dir():
    """Возвращает абсолютный путь до корня app/"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))

def load_json(relative_path: str):
    """Загружает JSON относительно корня app/"""
    base_dir = get_base_dir()
    full_path = os.path.join(base_dir, relative_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Файл не найден: {full_path}")
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)