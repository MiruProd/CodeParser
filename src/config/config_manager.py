import os
import json
from .resource_helper import get_resource_path


class ConfigManager:

    def __init__(self):
        if os.name == 'nt':
            self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'CodeParser')
        else:
            self.config_dir = os.path.expanduser('~/.config/CodeParser')

        self.config_path = os.path.join(self.config_dir, 'settings.json')
        self.default_config = self.load_json_resource("resources/default_settings.json")
        self.comment_rules = self.load_json_resource("resources/comment_rules.json")
        self.config = self.load_config()

    def load_json_resource(self, relative_path: str) -> dict:
        path = get_resource_path(relative_path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Отсутствует ресурс '{relative_path}' по пути {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения системного конфигурационного файла {relative_path}: {e}")

    def load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            modified = False
            for key, val in self.default_config.items():
                if key not in loaded:
                    loaded[key] = val
                    modified = True

            if modified:
                self.save_config(loaded)
            return loaded
        except Exception:
            self.save_config(self.default_config)
            return self.default_config

    def save_config(self, data=None):
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