# src/core/updater.py

import os
import sys
import subprocess
import requests
import zipfile
import tarfile
from PyQt6.QtCore import QThread, pyqtSignal

# Версия должна соответствовать вашим тегам в репозитории на GitHub
CURRENT_VERSION = "v1.0.2"

# Замените на путь к вашему репозиторию
GITHUB_REPO = "miruprod/CodeParser" 

class UpdateCheckerThread(QThread):
    """
    Фоновый поток для проверки наличия новой версии на GitHub.
    Анализирует платформу и ищет соответствующий ей релизный ассет.
    """
    check_finished = pyqtSignal(bool, str, str)

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            headers = {"User-Agent": "CodeParser-Updater"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name", "")
                
                # Определяем суффикс нужного ассета в зависимости от операционной системы
                target_suffix = ""
                if sys.platform == "win32":
                    target_suffix = "_Windows.exe"
                elif sys.platform == "darwin":
                    target_suffix = "_macOS.zip"
                elif sys.platform.startswith("linux"):
                    target_suffix = "_Linux.tar.gz"
                    
                download_url = ""
                for asset in data.get("assets", []):
                    asset_name = asset.get("name", "")
                    if target_suffix and asset_name.endswith(target_suffix):
                        download_url = asset.get("browser_download_url", "")
                        break
                
                # Сравниваем версии и проверяем, найден ли нужный файл
                if latest_tag and latest_tag != CURRENT_VERSION and download_url:
                    self.check_finished.emit(True, latest_tag, download_url)
                    return
                    
            self.check_finished.emit(False, CURRENT_VERSION, "")
        except Exception as e:
            print(f"Ошибка проверки обновлений: {e}")
            self.check_finished.emit(False, "", "")


def perform_self_update(download_url):
    """
    Этап 1: Скачивает архив/файл обновления и распаковывает его рядом.
    Возвращает: (успешно: bool, сообщение_или_ошибка: str, путь_к_новому_файлу: str)
    """
    try:
        current_exe = os.path.abspath(sys.argv[0])
        app_dir = os.path.dirname(current_exe)
        
        # Скачиваем ассет во временный буфер
        response = requests.get(download_url, stream=True, timeout=30)
        if response.status_code != 200:
            return False, f"Ошибка загрузки: HTTP {response.status_code}", ""

        # Сохраняем скачанный архив/файл во временную директорию
        asset_name = download_url.split("/")[-1]
        temp_download_path = os.path.join(app_dir, asset_name)
        
        with open(temp_download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Обработка и подготовка файлов под конкретную ОС
        if sys.platform == "win32":
            # На Windows мы скачиваем напрямую новый готовый EXE
            return True, "Обновление успешно скачано.", temp_download_path

        elif sys.platform.startswith("linux"):
            # На Linux распаковываем исполняемый файл из tar.gz
            new_binary_path = os.path.join(app_dir, "CodeParser_new")
            try:
                with tarfile.open(temp_download_path, "r:gz") as tar:
                    # Извлекаем только файл с именем CodeParser и переименовываем во временный
                    member = tar.getmember("CodeParser")
                    member.name = os.path.basename(new_binary_path)
                    tar.extract(member, path=app_dir)
                os.remove(temp_download_path)  # Удаляем архив
                return True, "Обновление успешно распаковано.", new_binary_path
            except Exception as e:
                return False, f"Ошибка распаковки архива Linux: {e}", ""

        elif sys.platform == "darwin":
            # На macOS автоматическая перезапись .app-директории во время работы
            # блокируется системой безопасности. Мы распакуем его рядом и откроем Finder.
            try:
                with zipfile.ZipFile(temp_download_path, 'r') as zip_ref:
                    zip_ref.extractall(app_dir)
                os.remove(temp_download_path)  # Удаляем архив
                
                # Открываем директорию в Finder, чтобы пользователь увидел распакованный файл
                subprocess.Popen(["open", app_dir])
                return True, (
                    f"Обновление успешно распаковано в папку:\n{app_dir}\n\n"
                    "Пожалуйста, закройте программу и запустите новую версию CodeParser.app из Finder."
                ), ""
            except Exception as e:
                return False, f"Ошибка распаковки архива macOS: {e}", ""

        return False, "Неподдерживаемая операционная система.", ""
    except Exception as e:
        return False, str(e), ""


def apply_restart_and_exit(new_file_path):
    """
    Этап 2: Выполняет подмену файлов в фоновом режиме и перезапускает программу.
    Вызывается ТОЛЬКО ПОСЛЕ того, как пользователь подтвердил перезапуск в графическом окне.
    """
    try:
        current_exe = os.path.abspath(sys.argv[0])
        
        if sys.platform == "win32":
            # Скрипт Windows ожидает завершения основного процесса, удаляет старый exe и переименовывает новый
            cmd = f'timeout /t 1 && del "{current_exe}" && move "{new_file_path}" "{current_exe}" && start "" "{current_exe}"'
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

        elif sys.platform.startswith("linux"):
            # Скрипт Linux делает то же самое и восстанавливает права на исполнение бинарника
            cmd = f'sleep 1 && mv "{new_file_path}" "{current_exe}" && chmod +x "{current_exe}" && "{current_exe}" &'
            subprocess.Popen(cmd, shell=True)
            sys.exit(0)

        elif sys.platform == "darwin":
            # На macOS мы уже открыли Finder и распаковали новую .app рядом, просто выходим
            sys.exit(0)
    except Exception as e:
        print(f"Ошибка при перезапуске приложения: {e}")
        sys.exit(1)