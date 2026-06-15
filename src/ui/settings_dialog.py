# src/ui/settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QLineEdit, QPushButton, QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

class ExtensionBadge(QPushButton):
    """
    Интерактивная кнопка-чипс для выбора расширения файла.
    Динамически меняет цвет при изменении состояния активности.
    """
    def __init__(self, text, active=True, parent=None):
        super().__init__(text, parent)
        self.extension = text
        self.active = active
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.toggle_active)

    def toggle_active(self):
        self.active = self.isChecked()
        self.update_style()

    def update_style(self):
        if self.active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: 1px solid #1177bb;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #1177bb; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #7f7f7f;
                    border: 1px solid #2d2d2d;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: normal;
                }
                QPushButton:hover { background-color: #4c4c4c; }
            """)


class SettingsDialog(QDialog):
    """Окно настройки автообновлений и активных расширений проекта."""
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Настройки CodeParser")
        self.setMinimumSize(500, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Раздел управления автообновлениями
        update_group = QGroupBox("Обновления")
        update_layout = QVBoxLayout(update_group)
        self.chk_auto_update = QCheckBox("Автоматически проверять обновления при запуске")
        self.chk_auto_update.setChecked(self.config_manager.get("auto_check_updates"))
        update_layout.addWidget(self.chk_auto_update)

        btn_manual_update = QPushButton("Проверить обновления сейчас")
        btn_manual_update.clicked.connect(self.trigger_parent_update)
        update_layout.addWidget(btn_manual_update)
        layout.addWidget(update_group)

        # 2. Раздел визуального переключения расширений (чипсы)
        ext_group = QGroupBox("Расширения файлов")
        ext_layout = QVBoxLayout(ext_group)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QFrame()
        self.badges_layout = QVBoxLayout(scroll_content)
        self.badges_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(scroll_content)
        ext_layout.addWidget(scroll)

        # Секция для быстрого добавления нового типа файлов в настройки
        add_layout = QHBoxLayout()
        self.new_ext_input = QLineEdit()
        self.new_ext_input.setPlaceholderText(".rs, .dart, .swift...")
        btn_add_ext = QPushButton("Добавить расширение")
        btn_add_ext.clicked.connect(self.add_new_extension)
        add_layout.addWidget(self.new_ext_input)
        add_layout.addWidget(btn_add_ext)
        ext_layout.addLayout(add_layout)
        
        layout.addWidget(ext_group, 1)

        # Кнопки сохранения и отмены изменений
        bottom_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить настройки")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)
        bottom_layout.addWidget(btn_cancel)
        layout.addLayout(bottom_layout)

        self.badges = []
        self.populate_badges()

    def populate_badges(self):
        """Очищает старые и перерисовывает кнопки-чипсы расширений."""
        # Удаляем старые кнопки
        for b in self.badges:
            b.deleteLater()
        self.badges.clear()

        # Полностью очищаем макет прокручиваемой зоны
        while self.badges_layout.count():
            child = self.badges_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        active_exts = self.config_manager.get("active_extensions", [])
        
        # Строим строки для размещения кнопок по горизонтали (по 5 элементов)
        row_widget = QFrame()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        count = 0
        for ext in active_exts:
            badge = ExtensionBadge(ext, active=True)
            row_layout.addWidget(badge)
            self.badges.append(badge)
            count += 1
            if count % 5 == 0:
                self.badges_layout.addWidget(row_widget)
                row_widget = QFrame()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        if count % 5 != 0:
            self.badges_layout.addWidget(row_widget)

    def add_new_extension(self):
        """Парсит и сохраняет новое расширение в список."""
        text = self.new_ext_input.text().strip().lower()
        if not text:
            return
        if not text.startswith('.'):
            text = '.' + text
            
        current_exts = self.config_manager.get("active_extensions", [])
        if text in current_exts:
            QMessageBox.information(self, "Инфо", f"Расширение {text} уже добавлено.")
            return

        current_exts.append(text)
        self.config_manager.set("active_extensions", current_exts)
        self.populate_badges()
        self.new_ext_input.clear()

    def trigger_parent_update(self):
        """Запускает ручную проверку обновлений через основное окно."""
        if self.parent() and hasattr(self.parent(), "check_for_updates_manual"):
            self.parent().check_for_updates_manual()

    def save_settings(self):
        """Передает обновленную конфигурацию для записи на диск."""
        active_list = [b.extension for b in self.badges if b.active]
        self.config_manager.set("active_extensions", active_list)
        self.config_manager.set("auto_check_updates", self.chk_auto_update.isChecked())
        self.accept()