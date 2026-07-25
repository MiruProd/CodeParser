import os
import sys


def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    entry_point = os.path.join(root_dir, "src", "main.py")
    dist_path = os.path.join(root_dir, "dist")
    build_path = os.path.join(root_dir, "build")
    icon_png = os.path.join(root_dir, "resources", "icons", "icon.png")

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
        "--collect-all=tiktoken",
        "--clean",
    ]

    if sys.platform == "win32":
        sys32_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll"]:
            dll_path = os.path.join(sys32_dir, dll_name)
            if os.path.exists(dll_path):
                args.append(f"--add-binary={dll_path};.")
                print(f"Config: Bundling MSVC runtime DLL: {dll_name}")
            else:
                print(f"Warning: System DLL not found: {dll_path}")

    resources_src = os.path.join(root_dir, "resources")
    if os.path.exists(resources_src):
        args.append(f"--add-data={resources_src}{os.pathsep}resources")
        print("Config: Found resources directory. Bundling as static asset folder.")
    else:
        print("Error: Resources directory not found! Build is broken.")
        sys.exit(1)

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