# build_scripts/build_exe.py

import os
import sys

def build():
    # Вычисляем корень проекта относительно папки со скриптом
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    entry_point = os.path.join(root_dir, "src", "main.py")
    dist_path = os.path.join(root_dir, "dist")
    build_path = os.path.join(root_dir, "build")
    icon_png = os.path.join(root_dir, "src", "ui", "icon.png")

    # Защитная проверка наличия установленного сборщика
    try:
        import PyInstaller
    except ImportError:
        print("Ошибка: Для сборки необходим пакет PyInstaller.")
        print("Пожалуйста, установите его командой: pip install pyinstaller")
        sys.exit(1)

    print("--- Начинается сборка исполняемого файла CodeParser ---")
    
    # Конфигурация сборки
    args = [
        entry_point,
        "--onefile",                 # Сборка в один автономный exe-файл
        "--noconsole",               # Подавление консольного окна при запуске GUI
        "--name=CodeParser",          # Название исполняемого файла
        f"--distpath={dist_path}",    # Директория для результирующего билда
        f"--workpath={build_path}",   # Директория для временных метаданных компиляции
        "--clean",                   # Принудительная очистка кэша компилятора
    ]

    # Если сгенерированный PNG логотип существует, передаем его сборщику
    if os.path.exists(icon_png):
        args.append(f"--icon={icon_png}")
        print("Параметр: Найдена иконка приложения. Устанавливаем логотип для EXE файла.")
    else:
        print("Параметр: Иконка PNG не обнаружена. EXE будет собран со стандартным логотипом.")

    # Добавление папки src в область видимости для корректного разрешения импортов
    src_dir = os.path.join(root_dir, "src")
    args.append(f"--paths={src_dir}")

    # Программный запуск сборки из API PyInstaller
    import PyInstaller.__main__
    PyInstaller.__main__.run(args)
    
    print("\n--- Процесс компиляции завершен! ---")
    print(f"Готовый файл находится по пути: {os.path.join(dist_path, 'CodeParser.exe')}")

if __name__ == "__main__":
    build()