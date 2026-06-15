# build_scripts/build_exe.py

import os
import sys

def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    entry_point = os.path.join(root_dir, "src", "main.py")
    dist_path = os.path.join(root_dir, "dist")
    build_path = os.path.join(root_dir, "build")
    icon_png = os.path.join(root_dir, "src", "ui", "icon.png")

    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller package is required for building.")
        print("Please install it using: pip install pyinstaller")
        sys.exit(1)

    print("--- Starting CodeParser executable build ---")
    
    args = [
        entry_point,
        "--onefile",
        "--noconsole",
        "--name=CodeParser",
        f"--distpath={dist_path}",
        f"--workpath={build_path}",
        "--clean",
    ]

    # Принудительно упаковываем библиотеки Microsoft Visual C++ Runtime (VCRuntime) вовнутрь EXE.
    # Это полностью решает проблему "Failed to load Python DLL" на компьютерах без установленного MSVC Redistributable.
    if sys.platform == "win32":
        sys32_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll"]:
            dll_path = os.path.join(sys32_dir, dll_name)
            if os.path.exists(dll_path):
                # На Windows PyInstaller требует разделения путей точкой с запятой ';'
                args.append(f"--add-binary={dll_path};.")
                print(f"Config: Bundling MSVC runtime DLL: {dll_name}")
            else:
                print(f"Warning: System DLL not found: {dll_path}")

    # Принудительно упаковываем статический шаблон настроек по умолчанию (default_settings.json)
    default_settings_src = os.path.join(root_dir, "src", "core", "default_settings.json")
    if os.path.exists(default_settings_src):
        # Используем кроссплатформенный разделитель путей (os.pathsep) для сборщика
        args.append(f"--add-data={default_settings_src}{os.pathsep}core")
        print("Config: Found default_settings.json. Bundling as static asset.")
    else:
        print("Error: default_settings.json not found! Build might be broken.")

    if os.path.exists(icon_png):
        args.append(f"--icon={icon_png}")
        print("Config: Application icon found. Setting logo for EXE file.")
    else:
        print("Config: PNG icon not found. EXE will be built with default logo.")

    src_dir = os.path.join(root_dir, "src")
    args.append(f"--paths={src_dir}")

    import PyInstaller.__main__
    PyInstaller.__main__.run(args)
    
    print("\n--- Compilation process finished! ---")
    print(f"Output file: {os.path.join(dist_path, 'CodeParser.exe')}")

if __name__ == "__main__":
    build()