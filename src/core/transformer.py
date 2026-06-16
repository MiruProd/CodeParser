# src/core/transformer.py

import re

class CodeTransformer:
    """
    Класс для оптимизации и минимизации исходного кода перед отправкой в LLM.
    Применяет правила разбора на основе внешней конфигурационной схемы.
    """

    @staticmethod
    def strip_comments(text: str, ext: str, comment_rules: dict) -> str:
        """
        Динамически удаляет комментарии, используя регулярные выражения
        из переданной схемы comment_rules.json.
        """
        ext = ext.lower()
        rules = comment_rules.get("rules", {})

        try:
            for rule_name, rule_data in rules.items():
                # Проверяем, относится ли расширение к текущей синтаксической группе
                if ext in rule_data.get("extensions", []):
                    
                    # Особая логика для Python (из-за наличия docstrings)
                    if rule_name == "python_style":
                        hash_pattern = rule_data.get("hash_pattern")
                        doc_pattern = rule_data.get("docstring_pattern")
                        
                        if hash_pattern:
                            def replace_python_hash(match):
                                # Возвращаем кавычки нетронутыми (группы 1 и 2)
                                if match.group(1): return match.group(1)
                                if match.group(2): return match.group(2)
                                # Сохраняем шебанг (#!/usr/bin/env python)
                                comment = match.group(3)
                                if comment and comment.startswith('#!'):
                                    return comment
                                return ""
                            text = re.sub(hash_pattern, replace_python_hash, text, flags=re.MULTILINE)
                        
                        if doc_pattern:
                            text = re.sub(doc_pattern, '', text, flags=re.MULTILINE)
                        return text
                    
                    # Стандартная логика для C-style, XML, SQL и Hash-style комментариев
                    else:
                        pattern = rule_data.get("pattern")
                        if not pattern:
                            continue
                            
                        def replace_standard(match):
                            # Пропускаем строковые литералы (группы 1 и 2)
                            if match.group(1): return match.group(1)
                            if match.group(2): return match.group(2)
                            return ""
                        
                        return re.sub(pattern, replace_standard, text, flags=re.MULTILINE | re.DOTALL)
                        
        except Exception as e:
            print(f"Ошибка при очистке комментариев для {ext}: {e}")
            
        return text

    @staticmethod
    def compress_whitespace(text: str) -> str:
        """
        Безопасно удаляет полностью пустые строки и пробелы на концах строк.
        Структурные отступы в начале строк полностью сохраняются.
        """
        lines = text.splitlines()
        compressed_lines = []
        
        for line in lines:
            cleaned_line = line.rstrip()
            if not cleaned_line:
                continue
            compressed_lines.append(cleaned_line)
            
        return "\n".join(compressed_lines)

    @classmethod
    def transform(cls, text: str, ext: str, comment_rules: dict, strip_comments_flag: bool, compress_whitespace_flag: bool) -> str:
        """
        Конвейер трансформации кода. Накладывает оптимизации на лету.
        """
        if strip_comments_flag:
            text = cls.strip_comments(text, ext, comment_rules)
        if compress_whitespace_flag:
            text = cls.compress_whitespace(text)
        return text