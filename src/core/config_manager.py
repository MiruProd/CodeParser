# src/core/config_manager.py

import os
import json

class ConfigManager:
    """
    Класс для управления конфигурацией приложения.
    Сохраняет настройки в формате JSON в директорию пользователя.
    """
    def __init__(self):
        # Определение кроссплатформенного пути для хранения настроек
        if os.name == 'nt':
            self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'CodeParser')
        else:
            self.config_dir = os.path.expanduser('~/.config/CodeParser')
            
        self.config_path = os.path.join(self.config_dir, 'settings.json')
        
        # Настройки по умолчанию
        self.default_config = {
            "use_gitignore": True,
            "ignore_binary": True,
            "ignore_lockfiles": True,
            "auto_check_updates": True,
            "theme": "Темная (VS Code)",
            "manual_excludes": (
                ".git, .idea, .vscode, build/bin, build/dist, "
                "node_modules, .venv, venv, dist, tmp, __pycache__"
            ),
            "active_extensions": [
                ".py", ".go", ".svelte", ".ts", ".js", ".css", ".html", 
                ".json", ".md", ".toml", ".yaml", ".yml", ".cpp", ".hpp", 
                ".c", ".h", ".rs", ".java", ".kt"
            ]
        }
        self.config = self.load_config()

    def load_config(self):
        """Загружает настройки из файла или создает дефолтные, если файла нет."""
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Заполняем новые поля, если они появились в дефолтной структуре
                for key, val in self.default_config.items():
                    if key not in loaded:
                        loaded[key] = val
                return loaded
        except Exception:
            return self.default_config

    def save_config(self, data=None):
        """Сохраняет текущую конфигурацию на диск."""
        if data:
            self.config = data
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # Выводим в консоль для отладки, если запись не удалась
            print(f"Ошибка сохранения настроек: {e}")

    def get(self, key, default=None):
        """Получает значение параметра по ключу."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Изменяет значение параметра и сохраняет настройки."""
        self.config[key] = value
        self.save_config()