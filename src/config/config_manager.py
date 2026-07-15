# src/config/config_manager.py

import os
import json
from .resource_helper import get_resource_path

class ConfigManager:
    """
    Класс для управления динамической конфигурацией приложения.
    Считывает шаблоны по умолчанию и синхронизирует их с профилем пользователя на диске.
    """
    def __init__(self):
        # Путь к папке пользователя
        if os.name == 'nt':
            self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'CodeParser')
        else:
            self.config_dir = os.path.expanduser('~/.config/CodeParser')
            
        self.config_path = os.path.join(self.config_dir, 'settings.json')
        
        # Динамическая загрузка статических ресурсов
        self.default_config = self.load_json_resource("resources/default_settings.json")
        self.comment_rules = self.load_json_resource("resources/comment_rules.json")
        
        self.config = self.load_config()

    def load_json_resource(self, relative_path: str) -> dict:
        """Безопасно загружает обязательный статический JSON-ресурс из папки приложения."""
        path = get_resource_path(relative_path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Критическая ошибка: отсутствует обязательный ресурс '{relative_path}' по пути {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Не удалось прочитать системный конфигурационный файл {relative_path}: {e}")

    def load_config(self) -> dict:
        """Загружает пользовательские настройки или инициализирует их дефолтными."""
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
            # Слияние новых ключей и умное объединение элементов списков (например, новых исключений)
            modified = False
            for key, val in self.default_config.items():
                if key not in loaded:
                    loaded[key] = val
                    modified = True
                elif isinstance(val, list) and isinstance(loaded[key], list):
                    for item in val:
                        if item not in loaded[key]:
                            loaded[key].append(item)
                            modified = True
                    
            if modified:
                self.save_config(loaded)
            return loaded
        except Exception:
            # Если пользовательский файл поврежден, перезаписываем его безопасной копией
            self.save_config(self.default_config)
            return self.default_config

    def save_config(self, data=None):
        """Записывает актуальные настройки в файл на диске пользователя."""
        if data is not None:
            self.config = data
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при записи пользовательских настроек: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()