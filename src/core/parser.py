# src/core/parser.py

import os
from .ignore_rules import is_ignored, parse_gitignore
from .transformer import CodeTransformer

class FileNode:
    """Промежуточная структура для изоляции логики дерева файлов от графической библиотеки."""
    def __init__(self, name, full_path, rel_path, is_dir, size=0):
        self.name = name
        self.full_path = full_path
        self.rel_path = rel_path
        self.is_dir = is_dir
        self.size = size
        self.children = []

def scan_directory(root_dir, use_gitignore, ignore_binary, ignore_lockfiles, whitelist_input_text, manual_input_text, output_file_path=None, gitignore_disabled_rules=None, binary_extensions=None, lockfiles_excludes=None):
    """Обходит проект на диске и возвращает отфильтрованное дерево FileNode с учетом всех динамических JSON-правил."""
    if not os.path.exists(root_dir):
        return None

    gitignore_rules = []
    if use_gitignore:
        all_rules = parse_gitignore(os.path.join(root_dir, '.gitignore'))
        if gitignore_disabled_rules:
            # Исключаем из обработки те правила, которые пользователь отключил в настройках
            gitignore_rules = [r for r in all_rules if r not in gitignore_disabled_rules]
        else:
            gitignore_rules = all_rules

    manual_excludes = [p.strip() for p in manual_input_text.split(',') if p.strip()]
    
    if ignore_lockfiles and lockfiles_excludes:
        manual_excludes.extend(lockfiles_excludes)
        
    whitelist = [ext.strip().lower() for ext in whitelist_input_text.split(',') if ext.strip()]

    root_node = FileNode(
        name=os.path.basename(root_dir),
        full_path=root_dir,
        rel_path='',
        is_dir=True
    )

    target_out_path = os.path.abspath(output_file_path) if output_file_path else None

    def _populate(parent_node, current_path):
        try:
            items = sorted(os.listdir(current_path), key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))
        except Exception:
            return

        for name in items:
            full_path = os.path.join(current_path, name)
            
            if target_out_path and os.path.abspath(full_path) == target_out_path:
                continue

            rel_path = os.path.relpath(full_path, root_dir)
            is_dir = os.path.isdir(full_path)

            if is_ignored(rel_path, gitignore_rules, manual_excludes, is_dir=is_dir):
                continue

            if not is_dir:
                _, ext = os.path.splitext(name)
                ext_lower = ext.lower()
                
                # Фильтруем бинарники на основе списка из JSON
                if ignore_binary and binary_extensions and (ext_lower in binary_extensions):
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
    """Рекурсивно строит ASCII структуру на основе переданных узлов."""
    lines = []
    
    if selected_paths:
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

def build_payload(root_dir, root_node, selected_files, selected_paths, 
                  comment_rules=None, strip_comments=False, compress_whitespace=False, 
                  system_prompt="", xml_format=True):
    """
    Генерирует финальный размеченный текст для экспорта.
    Поддерживает строгий XML-формат и стандартную текстовую разметку на лету.
    """
    if not root_node:
        return ""

    # Генерируем дерево структуры в виде ASCII-текста
    tree_lines = [os.path.basename(root_dir) + "/"]
    tree_lines.extend(generate_ascii_tree(root_node, selected_paths))
    ascii_tree = "\n".join(tree_lines)

    # 1. Сборка в строгом XML формате
    if xml_format:
        lines = ["<repository_context>\n"]
        
        # Раздел инструкций ИИ
        if system_prompt.strip():
            lines.append("  <instructions>\n")
            lines.append(f"    {system_prompt.strip()}\n")
            lines.append("  </instructions>\n\n")

        # Раздел структуры директорий
        lines.append("  <directory_structure>\n")
        lines.append(f"<![CDATA[\n{ascii_tree}\n]]>\n")
        lines.append("  </directory_structure>\n\n")

        # Раздел содержимого файлов
        lines.append("  <source_files>\n")
        if selected_files:
            for file_info in selected_files:
                rel_path = file_info["rel_path"]
                # Безопасно извлекаем расширение прямо из относительного пути к файлу
                _, ext = os.path.splitext(rel_path)
                
                lines.append(f'    <file path="{rel_path}">\n')
                try:
                    with open(file_info['full_path'], 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    # Применяем оптимизацию токенов, если включены флаги
                    if comment_rules and (strip_comments or compress_whitespace):
                        content = CodeTransformer.transform(
                            content, ext, comment_rules, strip_comments, compress_whitespace
                        )
                    
                    # Безопасно экранируем возможные закрывающие CDATA теги внутри исходного кода
                    safe_content = content.replace("]]>", "]]]]><![CDATA[>")
                    lines.append(f"<![CDATA[\n{safe_content}\n]]>\n")
                except Exception as e:
                    lines.append(f"<![CDATA[\n[Ошибка при чтении содержимого: {e}]\n]]>\n")
                lines.append('    </file>\n')
        lines.append("  </source_files>\n")
        lines.append("</repository_context>")
        
        return "".join(lines)

    # 2. Сборка в классическом текстовом формате (Markdown-стиль)
    else:
        lines = []
        if system_prompt.strip():
            lines.append("=== ИНСТРУКЦИЯ ДЛЯ НЕЙРОСЕТИ ===\n")
            lines.append(system_prompt.strip())
            lines.append("\n" + "="*80 + "\n\n")

        lines.append("=== ПОЛНАЯ СТРУКТУРА ПРОЕКТА (БЕЗ СИСТЕМНОГО МУСОРА) ===\n")
        lines.append(ascii_tree)
        lines.append("\n" + "="*80 + "\n\n")

        if selected_files:
            lines.append("=== СОДЕРЖИМОЕ КЛЮЧЕВЫХ ФАЙЛОВ КОДА ===\n\n")
            for file_info in selected_files:
                rel_path = file_info["rel_path"]
                _, ext = os.path.splitext(rel_path)
                
                lines.append(f'<file path="{rel_path}">\n')
                try:
                    with open(file_info['full_path'], 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    if comment_rules and (strip_comments or compress_whitespace):
                        content = CodeTransformer.transform(
                            content, ext, comment_rules, strip_comments, compress_whitespace
                        )
                    lines.append(content)
                except Exception as e:
                    lines.append(f"[Ошибка при чтении содержимого: {e}]")
                lines.append('\n</file>\n\n')
        else:
            lines.append("=== СОДЕРЖИМОЕ КОДА ===\n\n[Ни один файл кода не был выбран для экспорта. Скопирована только структура проекта.]\n")

        return "".join(lines)