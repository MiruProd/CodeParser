# src/core/updater.py

import os
import sys
import subprocess
import requests
from PyQt6.QtCore import QThread, pyqtSignal

CURRENT_VERSION = "v1.0.0"
GITHUB_REPO = "MiruProd/CodeParser" 

class UpdateCheckerThread(QThread):
    """
    Фоновый поток для проверки наличия новой версии на GitHub.
    Передает сигнал: (есть_ли_обновление, версия_на_сервере, url_скачивания_exe)
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
                
                # Поиск EXE-файла среди ассетов релиза
                download_url = ""
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url", "")
                        break
                
                # Сравниваем версии, если теги не совпадают
                if latest_tag and latest_tag != CURRENT_VERSION:
                    self.check_finished.emit(True, latest_tag, download_url)
                    return
                    
            self.check_finished.emit(False, CURRENT_VERSION, "")
        except Exception as e:
            print(f"Ошибка проверки обновлений: {e}")
            self.check_finished.emit(False, "", "")


def perform_self_update(download_url):
    """
    Скачивает обновленный исполняемый файл и подменяет текущий
    при помощи отложенной команды Windows CMD.
    """
    try:
        current_exe = os.path.abspath(sys.argv[0])
        if not current_exe.endswith(".exe"):
            return False, "Обновление доступно только для скомпилированной версии (.exe)"

        new_exe = current_exe.replace(".exe", "_new.exe")
        
        # Скачиваем файл во временный
        response = requests.get(download_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(new_exe, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            return False, f"Ошибка скачивания: HTTP {response.status_code}"

        # Запускаем отложенный скрипт CMD, который подождет завершения текущего процесса,
        # удалит его, переименует новый файл и запустит его.
        cmd = f'timeout /t 1 && del "{current_exe}" && move "{new_exe}" "{current_exe}" && start "" "{current_exe}"'
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Завершаем текущий процесс
        sys.exit(0)
    except Exception as e:
        return False, str(e)