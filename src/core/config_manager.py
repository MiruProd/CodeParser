# src/core/config_manager.py

import os
import json

class ConfigManager:
    """
    Класс для управления динамической конфигурацией приложения.
    Считывает шаблоны по умолчанию из файла default_settings.json и 
    синхронизирует их с пользовательским файлом настроек на диске.
    """
    def __init__(self):
        # Определение системного пути для хранения настроек пользователя
        if os.name == 'nt':
            self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'CodeParser')
        else:
            self.config_dir = os.path.expanduser('~/.config/CodeParser')
            
        self.config_path = os.path.join(self.config_dir, 'settings.json')
        
        # Загружаем статический шаблон по умолчанию
        self.default_config = self.load_default_settings()
        self.config = self.load_config()

    def load_default_settings(self):
        """Загружает шаблон настроек по умолчанию из статического файла JSON."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(current_dir, "default_settings.json")
        
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при чтении default_settings.json: {e}")
        
        # Минимальный резервный вариант, если статический шаблон не найден
        return {
            "use_gitignore": True,
            "ignore_binary": True,
            "ignore_lockfiles": True,
            "auto_check_updates": True,
            "theme": "Темная (VS Code)",
            "selected_preset": "Все текстовые файлы (без ограничений)",
            "global_excludes": [".git", "node_modules", ".venv", "venv", "__pycache__"],
            "active_extensions": [],
            "all_known_extensions": [".py", ".go", ".ts", ".js", ".html", ".css", ".json", ".md"],
            "presets": {
                "Все текстовые файлы (без ограничений)": []
            }
        }

    def load_config(self):
        """Загружает настройки из JSON или создает их на основе шаблона."""
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
            # Безопасное слияние ключей на случай обновления шаблонов
            modified = False
            for key, val in self.default_config.items():
                if key not in loaded:
                    loaded[key] = val
                    modified = True
                    
            if modified:
                self.save_config(loaded)
            return loaded
        except Exception:
            return self.default_config

    def save_config(self, data=None):
        """Записывает актуальные настройки в файл на диске."""
        if data:
            self.config = data
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            print(f"Лог: Настройки сохранены в: {self.config_path}")
        except Exception as e:
            print(f"Ошибка при записи настроек в JSON: {e}")

    def get(self, key, default=None):
        """Возвращает значение конфигурации по ключу."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Обновляет значение по ключу и сохраняет настройки."""
        self.config[key] = value
        self.save_config()