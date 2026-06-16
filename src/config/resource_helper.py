# src/config/resource_helper.py

import os
import sys

def get_resource_path(relative_path: str) -> str:
    """
    Возвращает абсолютный путь к ресурсу.
    Принимает относительный путь, например: 'resources/comment_rules.json'.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller распаковывает ресурсы во временную папку sys._MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    
    # В режиме разработки: поднимаемся на два уровня вверх от src/config/ к корню проекта
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, relative_path)