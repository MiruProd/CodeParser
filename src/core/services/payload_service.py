import os
from typing import List, Set, Dict, Any, Optional
from core.models.file_node import FileNode
from core.models.project_options import TransformOptions
from core.transformers.pipeline import TransformerPipeline


class PayloadService:

    @staticmethod
    def generate_ascii_tree(node: FileNode, selected_paths: Optional[Set[str]] = None, indent: str = "") -> List[str]:
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
                lines.extend(PayloadService.generate_ascii_tree(child, selected_paths, next_indent))

        return lines

    def build_payload(
        self,
        root_dir: str,
        root_node: FileNode,
        selected_files: List[Dict[str, Any]],
        selected_paths: Set[str],
        options: TransformOptions,
        pipeline: Optional[TransformerPipeline] = None
    ) -> str:
        if not root_node:
            return ""

        tree_lines = [os.path.basename(root_dir) + "/"]
        tree_paths = None if options.always_send_full_tree else selected_paths
        tree_lines.extend(self.generate_ascii_tree(root_node, tree_paths))
        ascii_tree = "\n".join(tree_lines)
        cdata_closer = "]" + "]>"
        cdata_find = "]" + "]>"
        cdata_replace = "]" + "]>]]><![CDATA["

        if options.xml_format:
            lines = ["<repository_context>\n"]

            if options.system_prompt.strip():
                lines.append("  <instructions>\n")
                lines.append(f"    {options.system_prompt.strip()}\n")
                lines.append("  </instructions>\n\n")

            lines.append("  <directory_structure>\n")
            lines.append(f"<![CDATA[\n{ascii_tree}\n{cdata_closer}\n")
            lines.append("  </directory_structure>\n\n")

            lines.append("  <source_files>\n")
            if selected_files:
                for file_info in selected_files:
                    rel_path = file_info["rel_path"]
                    _, ext = os.path.splitext(rel_path)

                    lines.append(f'    <file path="{rel_path}">\n')
                    try:
                        with open(file_info['full_path'], 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()

                        if pipeline:
                            content = pipeline.execute(content, ext)

                        safe_content = content.replace(cdata_find, cdata_replace)
                        lines.append(f"<![CDATA[\n{safe_content}\n{cdata_closer}\n")
                    except Exception as e:
                        lines.append(f"<![CDATA[\n[Ошибка при чтении содержимого: {e}]\n{cdata_closer}\n")
                    lines.append('    </file>\n')
            lines.append("  </source_files>\n")
            lines.append("</repository_context>")

            return "".join(lines)

        else:
            lines = []
            if options.system_prompt.strip():
                lines.append("=== ИНСТРУКЦИЯ ДЛЯ НЕЙРОСЕТИ ===\n")
                lines.append(options.system_prompt.strip())
                lines.append("\n" + "=" * 80 + "\n\n")

            lines.append("=== ПОЛНАЯ СТРУКТУРА ПРОЕКТА (БЕЗ СИСТЕМНОГО МУСОРА) ===\n")
            lines.append(ascii_tree)
            lines.append("\n" + "=" * 80 + "\n\n")

            if selected_files:
                lines.append("=== СОДЕРЖИМОЕ КЛЮЧЕВЫХ ФАЙЛОВ КОДА ===\n\n")
                for file_info in selected_files:
                    rel_path = file_info["rel_path"]
                    _, ext = os.path.splitext(rel_path)

                    lines.append(f'<file path="{rel_path}">\n')
                    try:
                        with open(file_info['full_path'], 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()

                        if pipeline:
                            content = pipeline.execute(content, ext)

                        lines.append(content)
                    except Exception as e:
                        lines.append(f"[Ошибка при чтении содержимого: {e}]")
                    lines.append('\n</file>\n\n')
            else:
                lines.append("=== СОДЕРЖИМОЕ КОДА ===\n\n[Ни один файл кода не был выбран для экспорта. Скопирована только структура проекта.]\n")

            return "".join(lines)