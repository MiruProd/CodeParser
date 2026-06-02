# src/core/ignore_rules.py

import os
import fnmatch

def parse_gitignore(gitignore_path):
    rules = []
    if not os.path.exists(gitignore_path):
        return rules
    try:
        with open(gitignore_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                rules.append(line)
    except Exception:
        # Игнорируем ошибки доступа, так как наличие .gitignore опционально
        pass
    return rules

def is_ignored(rel_path, gitignore_rules, manual_excludes, is_dir=False):
    # Приведение к Unix-формату для кроссплатформенного сопоставления путей
    unix_path = rel_path.replace('\\', '/')
    parts = unix_path.split('/')
    
    # 1. Проверка пользовательских исключений
    for pattern in manual_excludes:
        pattern = pattern.strip()
        if not pattern:
            continue
        if pattern in parts:
            return True
        if fnmatch.fnmatch(unix_path, pattern) or fnmatch.fnmatch(parts[-1], pattern):
            return True
            
    # 2. Эмуляция логики Git без привлечения тяжелых сторонних библиотек (например, pathspec)
    for rule in gitignore_rules:
        is_dir_rule = rule.endswith('/')
        if is_dir_rule and not is_dir:
            continue
            
        clean_rule = rule.rstrip('/')
        
        # Если в правиле есть слэш, сопоставляем от корня, иначе проверяем по сегментам
        if '/' in clean_rule:
            if clean_rule.startswith('/'):
                anchored_rule = clean_rule[1:]
            else:
                anchored_rule = clean_rule
            
            if fnmatch.fnmatch(unix_path, anchored_rule) or unix_path.startswith(anchored_rule + '/'):
                return True
        else:
            for part in parts:
                if fnmatch.fnmatch(part, clean_rule):
                    return True
            if fnmatch.fnmatch(unix_path, clean_rule):
                return True
                
    return False