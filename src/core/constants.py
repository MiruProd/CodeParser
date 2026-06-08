# src/core/constants.py

UNIVERSAL_GLOBAL_EXCLUDES = (
    ".git, .github, .idea, .vscode, build/bin, build/dist, "
    "node_modules, .vite, .svelte-kit, .next, venv, .venv, env, .env, "
    "dist, tmp, temp, __pycache__"
)

# Токены лок-файлов и автогенерации, которые засоряют контекст LLM и не несут полезной логики
BOILERPLATE_LOCKFILES_EXCLUDES = (
    "package-lock.json, package-lock.json.md5, yarn.lock, pnpm-lock.yaml, "
    "go.sum, zgotext.go, locales, wailsjs, *.gotext.json, COPYING, LICENSE"
)

BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', 
    '.exe', '.dll', '.bin', '.zip', '.tar', '.gz', '.tgz', 
    '.rar', '.7z', '.mp3', '.mp4', '.wav', '.avi', '.mov', 
    '.woff', '.woff2', '.ttf', '.eot', '.otf', '.db', '.sqlite', 
    '.sqlite3', '.dmg', '.iso', '.msi', '.pkg', '.sys', '.cab', 
    '.psd', '.class', '.pyc', '.o', '.obj', '.so', '.dylib', '.suo', '.svg'
}

PRESETS = {
    "Все текстовые файлы (без ограничений)": "",
    "Go / Wails / Svelte": ".go, .svelte, .ts, .js, .css, .html, .json, .md, .toml, .yaml, .yml",
    "Web / Frontend (React / Vue / TS)": ".ts, .tsx, .js, .jsx, .svelte, .vue, .html, .css, .json, .md, .yaml, .yml",
    "Python": ".py, .ipynb, .md, .txt, .json, .yaml, .yml, .ini, .toml",
    "Rust": ".rs, .toml, .md",
    "C / C++": ".cpp, .hpp, .c, .h, .md, .cmake, Makefile",
    "Java / Kotlin": ".java, .kt, .kts, .xml, .gradle, .properties, .md"
}