import os
import fnmatch


def parse_gitignore(gitignore_path: str) -> list:
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
        pass
    return rules


def is_ignored(rel_path: str, gitignore_rules: list, manual_excludes: list, is_dir: bool = False) -> bool:
    unix_path = rel_path.replace('\\', '/')
    parts = unix_path.split('/')

    for pattern in manual_excludes:
        pattern = pattern.strip()
        if not pattern:
            continue
        if pattern in parts:
            return True
        if fnmatch.fnmatch(unix_path, pattern) or fnmatch.fnmatch(parts[-1], pattern):
            return True

    for rule in gitignore_rules:
        is_dir_rule = rule.endswith('/')
        if is_dir_rule and not is_dir:
            continue

        clean_rule = rule.rstrip('/')

        if '/' in clean_rule:
            anchored_rule = clean_rule[1:] if clean_rule.startswith('/') else clean_rule
            if fnmatch.fnmatch(unix_path, anchored_rule) or unix_path.startswith(anchored_rule + '/'):
                return True
        else:
            for part in parts:
                if fnmatch.fnmatch(part, clean_rule):
                    return True
            if fnmatch.fnmatch(unix_path, clean_rule):
                return True

    return False