# src/ui/style.py

# Семантическая палитра для темной темы (VS Code Dark Style)
DARK_PALETTE = {
    "bg_main": "#1e1e1e",
    "bg_widget": "#252526",
    "bg_header": "#2d2d2d",
    "fg_main": "#d4d4d4",
    "fg_muted": "#7f7f7f",
    "border": "#3c3c3c",
    "accent": "#0e639c",
    "accent_hover": "#1177bb",
    "accent_disabled": "#3c3c3c",
    "fg_accent": "#ffffff"
}

# Семантическая палитра для светлой темы (Modern Light Flat Style)
LIGHT_PALETTE = {
    "bg_main": "#f3f3f3",
    "bg_widget": "#ffffff",
    "bg_header": "#e4e4e7",
    "fg_main": "#1f1f1f",
    "fg_muted": "#71717a",
    "border": "#d4d4d8",
    "accent": "#0f62fe",
    "accent_hover": "#0353e9",
    "accent_disabled": "#e0e0e0",
    "fg_accent": "#ffffff"
}

def get_stylesheet(palette: dict) -> str:
    """
    Генерирует QSS-таблицу стилей на основе переданной семантической палитры.
    Избавляет от дублирования цветовых кодов и упрощает динамическое переключение тем.
    """
    return f"""
    QMainWindow, QWidget {{ 
        background-color: {palette['bg_main']}; 
        color: {palette['fg_main']}; 
    }}

    QGroupBox {{ 
        border: 1px solid {palette['border']}; 
        border-radius: 6px; 
        margin-top: 10px; 
        padding: 10px; 
        font-weight: bold; 
    }}

    QGroupBox::title {{ 
        subcontrol-origin: margin; 
        left: 8px; 
        padding: 0 3px; 
    }}

    QPushButton {{ 
        background-color: {palette['accent']}; 
        color: {palette['fg_accent']}; 
        border: none; 
        padding: 6px 12px; 
        border-radius: 4px; 
        font-weight: bold; 
        font-size: 11px; 
    }}

    QPushButton:hover {{ 
        background-color: {palette['accent_hover']}; 
    }}

    QPushButton:disabled {{ 
        background-color: {palette['accent_disabled']}; 
        color: {palette['fg_muted']}; 
    }}

    QLineEdit, QTextEdit, QComboBox {{ 
        background-color: {palette['bg_widget']}; 
        border: 1px solid {palette['border']}; 
        border-radius: 4px; 
        color: {palette['fg_main']}; 
        padding: 5px; 
    }}

    QTreeWidget {{ 
        background-color: {palette['bg_widget']}; 
        border: 1px solid {palette['border']}; 
        color: {palette['fg_main']}; 
    }}

    QHeaderView::section {{ 
        background-color: {palette['bg_header']}; 
        color: {palette['fg_main']}; 
        border: 1px solid {palette['border']}; 
        padding: 4px; 
    }}

    QStatusBar {{ 
        background-color: {palette['accent']}; 
        color: {palette['fg_accent']}; 
    }}
    """