# src/core/parser.py

import os
from .ignore_rules import is_ignored, parse_gitignore
from .constants import BINARY_EXTENSIONS, BOILERPLATE_LOCKFILES_EXCLUDES

class FileNode:
    """Промежуточная структура для изоляции логики дерева файлов от графической библиотеки."""
    def __init__(self, name, full_path, rel_path, is_dir, size=0):
        self.name = name
        self.full_path = full_path
        self.rel_path = rel_path
        self.is_dir = is_dir
        self.size = size
        self.children = []

def scan_directory(root_dir, use_gitignore, ignore_binary, ignore_lockfiles, whitelist_input_text, manual_input_text):
    """Обходит проект на диске и возвращает отфильтрованное дерево FileNode."""
    if not os.path.exists(root_dir):
        return None

    gitignore_rules = []
    if use_gitignore:
        gitignore_rules = parse_gitignore(os.path.join(root_dir, '.gitignore'))

    manual_excludes = [p.strip() for p in manual_input_text.split(',') if p.strip()]
    
    if ignore_lockfiles:
        lockfiles_rules = [p.strip() for p in BOILERPLATE_LOCKFILES_EXCLUDES.split(',') if p.strip()]
        manual_excludes.extend(lockfiles_rules)
        
    whitelist = [ext.strip().lower() for ext in whitelist_input_text.split(',') if ext.strip()]

    root_node = FileNode(
        name=os.path.basename(root_dir),
        full_path=root_dir,
        rel_path='',
        is_dir=True
    )

    def _populate(parent_node, current_path):
        try:
            # Сортируем: сначала директории, затем файлы по алфавиту для предсказуемости вывода
            items = sorted(os.listdir(current_path), key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))
        except Exception:
            # Молча пропускаем системные директории и битые символические ссылки
            return

        for name in items:
            full_path = os.path.join(current_path, name)
            rel_path = os.path.relpath(full_path, root_dir)
            is_dir = os.path.isdir(full_path)

            if is_ignored(rel_path, gitignore_rules, manual_excludes, is_dir=is_dir):
                continue

            if not is_dir:
                _, ext = os.path.splitext(name)
                ext_lower = ext.lower()
                if ignore_binary and ext_lower in BINARY_EXTENSIONS:
                    continue
                if whitelist and ext_lower not in whitelist:
                    continue

            size = 0 if is_dir else os.path.getsize(full_path)
            child_node = FileNode(name, full_path, rel_path.replace('\\', '/'), is_dir, size)
            parent_node.children.append(child_node)

            if is_dir:
                _populate(child_node, full_path)

    _populate(root_node, root_dir)
    return root_node

def generate_ascii_tree(node, selected_paths=None, indent=""):
    """Рекурсивно строит ASCII структуру.
    Если передан selected_paths, дерево усекается только до выбранных пользователем элементов.
    """
    lines = []
    
    if selected_paths is not None:
        # Отображаем только те узлы, чьи пути (или пути их потомков) выбраны пользователем
        children = [
            c for c in node.children 
            if c.rel_path in selected_paths or (c.is_dir and any(p.startswith(c.rel_path + '/') for p in selected_paths))
        ]
    else:
        children = node.children

    num_children = len(children)
    for idx, child in enumerate(children):
        is_last = (idx == num_children - 1)
        prefix = "└── " if is_last else "├── "
        next_indent = indent + ("    " if is_last else "│   ")

        display_name = child.name + "/" if child.is_dir else child.name
        lines.append(f"{indent}{prefix}{display_name}")

        if child.is_dir:
            lines.extend(generate_ascii_tree(child, selected_paths, next_indent))

    return lines

def build_payload(root_dir, root_node, selected_files, selected_paths):
    """Генерирует финальный размеченный текст для экспорта."""
    if not root_node:
        return ""

    lines = []
    
    # 1. Структура проекта на основе текущего выбора в GUI
    lines.append("=== ПОЛНАЯ СТРУКТУРА ПРОЕКТА (БЕЗ СИСТЕМНОГО МУСОРА) ===\n")
    lines.append(os.path.basename(root_dir) + "/")
    lines.extend(generate_ascii_tree(root_node, selected_paths))
    lines.append("\n" + "="*80 + "\n\n")

    # 2. XML-подобная разметка содержимого файлов для лучшего понимания контекста LLM
    if selected_files:
        lines.append("=== СОДЕРЖИМОЕ КЛЮЧЕВЫХ ФАЙЛОВ КОДА ===\n\n")
        for file_info in selected_files:
            lines.append(f'<file path="{file_info["rel_path"]}">\n')
            try:
                # errors='replace' спасает от падения на экзотических или поврежденных кодировках
                with open(file_info['full_path'], 'r', encoding='utf-8', errors='replace') as f:
                    lines.append(f.read())
            except Exception as e:
                lines.append(f"[Ошибка при чтении содержимого: {e}]\n")
            lines.append('\n</file>\n\n')
    else:
        lines.append("=== СОДЕРЖИМОЕ КОДА ===\n\n[Ни один файл кода не был выбран для экспорта. Скопирована только структура проекта.]\n")

    return "".join(lines)