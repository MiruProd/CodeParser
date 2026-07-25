import os
import subprocess
from typing import Tuple, Set


class GitService:

    @staticmethod
    def get_modified_files(root_dir: str) -> Tuple[bool, str, Set[str]]:
        if not root_dir or not os.path.exists(root_dir):
            return False, "Папка проекта не найдена.", set()

        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            modified_files = set()
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    path_part = line[3:].strip()
                    if " -> " in path_part:
                        path_part = path_part.split(" -> ")[-1].strip()
                    path_part = path_part.strip('"\'')
                    normalized_path = path_part.replace('\\', '/')
                    modified_files.add(normalized_path)

            if not modified_files:
                return False, "Нет измененных файлов в репозитории Git.", set()

            return True, f"Найдено измененных файлов Git: {len(modified_files)}", modified_files
        except Exception as e:
            return False, f"Ошибка выполнения команды Git: {e}", set()

    @staticmethod
    def get_git_diff(root_dir: str, context_lines: int = 3) -> Tuple[bool, str]:
        if not root_dir or not os.path.exists(root_dir):
            return False, "Папка проекта не найдена."

        try:
            res = subprocess.run(
                ["git", "diff", f"-U{context_lines}"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            diff_text = res.stdout.strip()
            if not diff_text:
                return False, "Нет изменений для создания Git Diff."

            return True, diff_text
        except Exception as e:
            return False, f"Ошибка получения Git Diff: {e}"