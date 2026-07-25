import os
import fnmatch
from typing import List, Optional
from core.models.file_node import FileNode
from core.models.project_options import ScanOptions


class ScannerService:

    @staticmethod
    def parse_gitignore(gitignore_path: str) -> List[str]:
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

    @staticmethod
    def is_ignored(rel_path: str, gitignore_rules: List[str], manual_excludes: List[str], is_dir: bool = False) -> bool:
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

    def scan(self, root_dir: str, options: ScanOptions) -> Optional[FileNode]:
        if not os.path.exists(root_dir):
            return None

        gitignore_rules = []
        if options.use_gitignore:
            all_rules = self.parse_gitignore(os.path.join(root_dir, '.gitignore'))
            if options.gitignore_disabled_rules:
                gitignore_rules = [r for r in all_rules if r not in options.gitignore_disabled_rules]
            else:
                gitignore_rules = all_rules

        manual_excludes = list(options.manual_excludes)
        if options.ignore_lockfiles and options.lockfiles_excludes:
            manual_excludes.extend(options.lockfiles_excludes)

        whitelist = [ext.strip().lower() for ext in options.whitelist_extensions if ext.strip()]

        root_node = FileNode(
            name=os.path.basename(root_dir),
            full_path=root_dir,
            rel_path='',
            is_dir=True
        )

        target_out_path = os.path.abspath(options.output_file_path) if options.output_file_path else None

        def _populate(parent_node: FileNode, current_path: str):
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

                if self.is_ignored(rel_path, gitignore_rules, manual_excludes, is_dir=is_dir):
                    continue

                if not is_dir:
                    _, ext = os.path.splitext(name)
                    ext_lower = ext.lower()

                    if options.ignore_binary and options.binary_extensions and (ext_lower in options.binary_extensions):
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