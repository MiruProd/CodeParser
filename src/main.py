# src/main.py

import sys
import os

if sys.platform == 'win32':
    import ctypes
    try:
        # Гарантируем корректность относительных импортов при упаковке в EXE через PyInstaller
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("miruprod.codeparser.gui.1.0")
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from ui.main_window import PackerApp

def main():
    app = QApplication(sys.argv)
    window = PackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()