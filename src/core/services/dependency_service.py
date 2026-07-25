import os
import re
from typing import Set


class DependencyService:

    PYTHON_IMPORT_REGEX = re.compile(
        r'^\s*(?:from|import)\s+(\.?\.?[a-zA-Z0-9_.]+)', re.MULTILINE
    )
    JS_TS_IMPORT_REGEX = re.compile(
        r'(?:import\s+.*?\s+from\s+["\'](\..*?)["\']|require\(["\'](\..*?)["\']\))'
    )
    CPP_IMPORT_REGEX = re.compile(
        r'^\s*#include\s+["\']([^"\']+)["\']', re.MULTILINE
    )
    RUST_MOD_REGEX = re.compile(
        r'^\s*(?:pub\s+)?mod\s+([a-zA-Z0-9_]+);', re.MULTILINE
    )

    def trace_dependencies(self, root_dir: str, target_rel_path: str) -> Set[str]:
        if not root_dir or not target_rel_path:
            return set()

        full_target_path = os.path.join(root_dir, target_rel_path)
        if not os.path.exists(full_target_path) or os.path.isdir(full_target_path):
            return set()

        try:
            with open(full_target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return set()

        _, ext = os.path.splitext(target_rel_path)
        ext = ext.lower()
        found_rel_paths = set()
        target_dir = os.path.dirname(full_target_path)

        if ext == '.py':
            matches = self.PYTHON_IMPORT_REGEX.findall(content)
            possible_roots = [
                root_dir,
                os.path.join(root_dir, 'src'),
                target_dir
            ]

            for raw_import in matches:
                # Обработка относительных импортов (начинающихся с точек)
                dot_count = len(raw_import) - len(raw_import.lstrip('.'))
                module_part = raw_import.lstrip('.')

                if dot_count > 0:
                    base_dir = target_dir
                    for _ in range(dot_count - 1):
                        base_dir = os.path.dirname(base_dir)
                    search_bases = [base_dir]
                else:
                    search_bases = possible_roots

                subpath = module_part.replace('.', '/') if module_part else ''

                for base in search_bases:
                    if subpath:
                        cand1 = os.path.join(base, f"{subpath}.py")
                        cand2 = os.path.join(base, subpath, "__init__.py")
                    else:
                        cand1 = ""
                        cand2 = os.path.join(base, "__init__.py")

                    if cand1 and os.path.isfile(cand1):
                        found_rel_paths.add(os.path.relpath(cand1, root_dir).replace('\\', '/'))
                        break
                    elif cand2 and os.path.isfile(cand2):
                        found_rel_paths.add(os.path.relpath(cand2, root_dir).replace('\\', '/'))
                        break

        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
            raw_matches = self.JS_TS_IMPORT_REGEX.findall(content)
            for m in raw_matches:
                rel_import = m[0] or m[1]
                if not rel_import:
                    continue
                abs_base = os.path.normpath(os.path.join(target_dir, rel_import))

                for possible_ext in ['', '.js', '.ts', '.jsx', '.tsx', '/index.js', '/index.ts']:
                    test_path = abs_base + possible_ext
                    if os.path.exists(test_path) and os.path.isfile(test_path):
                        found_rel_paths.add(os.path.relpath(test_path, root_dir).replace('\\', '/'))
                        break

        elif ext in ('.c', '.cpp', '.h', '.hpp'):
            matches = self.CPP_IMPORT_REGEX.findall(content)
            for header_file in matches:
                test_path_1 = os.path.join(target_dir, header_file)
                test_path_2 = os.path.join(root_dir, header_file)

                if os.path.exists(test_path_1) and os.path.isfile(test_path_1):
                    found_rel_paths.add(os.path.relpath(test_path_1, root_dir).replace('\\', '/'))
                elif os.path.exists(test_path_2) and os.path.isfile(test_path_2):
                    found_rel_paths.add(os.path.relpath(test_path_2, root_dir).replace('\\', '/'))

        elif ext == '.rs':
            matches = self.RUST_MOD_REGEX.findall(content)
            for mod_name in matches:
                candidate_1 = os.path.join(target_dir, f"{mod_name}.rs")
                candidate_2 = os.path.join(target_dir, mod_name, "mod.rs")

                if os.path.exists(candidate_1) and os.path.isfile(candidate_1):
                    found_rel_paths.add(os.path.relpath(candidate_1, root_dir).replace('\\', '/'))
                elif os.path.exists(candidate_2) and os.path.isfile(candidate_2):
                    found_rel_paths.add(os.path.relpath(candidate_2, root_dir).replace('\\', '/'))

        return found_rel_paths