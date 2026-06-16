# src/config/prompt_manager.py

import os
import json

class PromptManager:
    """
    Класс для управления шаблонами системных инструкций (промптов) и интерактивными правилами-карточками.
    """
    def __init__(self, config_dir, config_manager):
        self.config_dir = config_dir
        self.config_manager = config_manager
        self.prompts_path = os.path.join(self.config_dir, 'prompts.json')
        self.rules_path = os.path.join(self.config_dir, 'rules.json')
        
        # Динамически считываем статические JSON-ресурсы через ConfigManager
        self.default_prompts = self.config_manager.load_json_resource("resources/default_prompts.json")
        self.default_rules = self.config_manager.load_json_resource("resources/default_rules.json")
        
        self.prompts = self.load_prompts()
        self.rules = self.load_rules()

    def load_prompts(self) -> dict:
        """Загружает шаблоны скиллов из локальной папки пользователя или инициализирует дефолтными."""
        if not os.path.exists(self.prompts_path):
            self.save_prompts(self.default_prompts)
            return self.default_prompts
        try:
            with open(self.prompts_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            modified = False
            for key, val in self.default_prompts.items():
                if key not in loaded:
                    loaded[key] = val
                    modified = True
            
            if modified:
                self.save_prompts(loaded)
            return loaded
        except Exception as e:
            print(f"Ошибка загрузки пользовательских prompts.json: {e}")
            return self.default_prompts

    def save_prompts(self, data=None):
        """Записывает измененные шаблоны скиллов на диск пользователя."""
        if data is not None:
            self.prompts = data
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.prompts_path, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка записи пользовательских настроек промптов: {e}")

    def load_rules(self) -> dict:
        """Загружает правила-карточки пользователя или инициализирует дефолтными."""
        if not os.path.exists(self.rules_path):
            self.save_rules(self.default_rules)
            return self.default_rules
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            # Синхронизация: если в эталон добавились новые правила, безопасно дописываем их
            modified = False
            for category, rules_list in self.default_rules.items():
                if category not in loaded:
                    loaded[category] = rules_list
                    modified = True
                else:
                    loaded_ids = {rule["id"] for rule in loaded[category]}
                    for rule in rules_list:
                        if rule["id"] not in loaded_ids:
                            loaded[category].append(rule)
                            modified = True
            
            if modified:
                self.save_rules(loaded)
            return loaded
        except Exception as e:
            print(f"Ошибка загрузки пользовательских rules.json: {e}")
            return self.default_rules

    def save_rules(self, data=None):
        """Записывает измененные правила-карточки на диск пользователя."""
        if data is not None:
            self.rules = data
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.rules_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка записи пользовательских настроек правил: {e}")

    def update_prompt(self, key, new_prompt_text):
        """Обновляет текст выбранного промпта и помечает его как пользовательский (custom)."""
        if key in self.prompts:
            self.prompts[key]["prompt"] = new_prompt_text
            self.prompts[key]["custom"] = True
            self.save_prompts()

    def add_custom_rule(self, category, title, description, rule_text) -> dict:
        """Добавляет новое кастомное правило в указанную категорию и сохраняет его на диск."""
        if category not in self.rules:
            self.rules[category] = []
        
        import time
        new_id = f"custom_rule_{int(time.time())}"
        new_rule = {
            "id": new_id,
            "title": title,
            "description": description,
            "rule_text": rule_text,
            "active": True
        }
        self.rules[category].append(new_rule)
        self.save_rules()
        return new_rule

    def compile_prompt(self, selected_rules_by_category: dict) -> str:
        """
        Собирает финальный структурированный XML-промпт на основе переданного словаря активных правил.
        selected_rules_by_category имеет структуру: { 'category_name': [rule_text_1, rule_text_2...], ... }
        """
        lines = []
        
        # Сопоставляем внутренние ключи категорий с красивыми XML тегами
        categories_mapping = {
            "system_role": "expert_role",
            "interaction_protocol": "interaction_protocol",
            "quality_standards": "code_generation_standards",
            "version_alignment": "technology_alignment"
        }
        
        for json_key, xml_tag in categories_mapping.items():
            rules_list = selected_rules_by_category.get(json_key, [])
            if rules_list:
                lines.append(f"<{xml_tag}>")
                for rule_text in rules_list:
                    lines.append(f"  - {rule_text}")
                lines.append(f"</{xml_tag}>\n")
                
        return "\n".join(lines).strip()