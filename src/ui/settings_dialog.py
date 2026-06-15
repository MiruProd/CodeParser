# src/ui/settings_dialog.py

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QLineEdit, QPushButton, QGroupBox, QScrollArea, QFrame, 
    QMessageBox, QTabWidget, QComboBox, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt

class BadgeButton(QPushButton):
    """
    Универсальная интерактивная кнопка-чипс для визуального
    выбора расширений, папок или правил .gitignore.
    """
    def __init__(self, text, active=True, parent=None):
        super().__init__(text, parent)
        self.item_text = text
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
                    padding: 5px 12px;
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
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: normal;
                }
                QPushButton:hover { background-color: #4c4c4c; }
            """)


class SettingsDialog(QDialog):
    """Единое интерактивное окно настроек с 4 вкладками (включая гибкую настройку .gitignore)."""
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Настройки CodeParser")
        self.setMinimumSize(600, 500)
        
        # Гарантируем наличие баз исключений в JSON
        if not self.config_manager.get("all_known_excludes"):
            self.config_manager.set("all_known_excludes", list(self.config_manager.get("global_excludes")))
        if not self.config_manager.get("gitignore_disabled_rules"):
            self.config_manager.set("gitignore_disabled_rules", [])

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Контейнер вкладок
        self.tabs = QTabWidget()
        
        self.tab_general = QWidget()
        self.tab_extensions = QWidget()
        self.tab_excludes = QWidget()
        self.tab_gitignore = QWidget()
        
        self.tabs.addTab(self.tab_general, "Общие")
        self.tabs.addTab(self.tab_extensions, "Расширения файлов")
        self.tabs.addTab(self.tab_excludes, "Папки-исключения")
        self.tabs.addTab(self.tab_gitignore, "Исключения .gitignore")
        
        self._build_general_tab()
        self._build_extensions_tab()
        self._build_excludes_tab()
        self._build_gitignore_tab()
        
        main_layout.addWidget(self.tabs)

        # Нижняя панель действий
        bottom_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить настройки")
        btn_save.clicked.connect(self.save_all_settings)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)
        bottom_layout.addWidget(btn_cancel)
        main_layout.addLayout(bottom_layout)

    def _build_general_tab(self):
        layout = QVBoxLayout(self.tab_general)

        filters_group = QGroupBox("Параметры фильтрации на диске")
        filters_layout = QVBoxLayout(filters_group)
        
        self.chk_gitignore = QCheckBox("Использовать правила .gitignore")
        self.chk_gitignore.setChecked(self.config_manager.get("use_gitignore"))
        filters_layout.addWidget(self.chk_gitignore)

        self.chk_ignore_binary = QCheckBox("Игнорировать бинарные файлы (изображения, архивы)")
        self.chk_ignore_binary.setChecked(self.config_manager.get("ignore_binary"))
        filters_layout.addWidget(self.chk_ignore_binary)

        self.chk_ignore_lockfiles = QCheckBox("Игнорировать лок-файлы и автогенерацию")
        self.chk_ignore_lockfiles.setChecked(self.config_manager.get("ignore_lockfiles"))
        filters_layout.addWidget(self.chk_ignore_lockfiles)
        
        layout.addWidget(filters_group)

        system_group = QGroupBox("Оформление и обновления")
        system_layout = QVBoxLayout(system_group)
        
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема интерфейса:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Темная (VS Code)", "Светлая"])
        self.combo_theme.setCurrentText(self.config_manager.get("theme"))
        theme_layout.addWidget(self.combo_theme)
        system_layout.addLayout(theme_layout)

        self.chk_auto_update = QCheckBox("Автоматически проверять новые версии при запуске")
        self.chk_auto_update.setChecked(self.config_manager.get("auto_check_updates"))
        system_layout.addWidget(self.chk_auto_update)

        btn_manual_update = QPushButton("Проверить наличие обновлений сейчас")
        btn_manual_update.clicked.connect(self.trigger_parent_update)
        system_layout.addWidget(btn_manual_update)
        
        layout.addWidget(system_group)
        layout.addStretch()

    def _build_extensions_tab(self):
        layout = QVBoxLayout(self.tab_extensions)

        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Пресет расширений:"))
        self.combo_presets = QComboBox()
        presets_data = self.config_manager.get("presets", {})
        self.combo_presets.addItems(list(presets_data.keys()))
        self.combo_presets.setCurrentText(self.config_manager.get("selected_preset"))
        self.combo_presets.currentTextChanged.connect(self.on_preset_selected)
        preset_layout.addWidget(self.combo_presets, 1)
        layout.addLayout(preset_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QFrame()
        self.ext_grid_layout = QGridLayout(scroll_content)
        self.ext_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        add_layout = QHBoxLayout()
        self.new_ext_input = QLineEdit()
        self.new_ext_input.setPlaceholderText(".rs, .dart, .swift...")
        btn_add_ext = QPushButton("Добавить расширение")
        btn_add_ext.clicked.connect(self.add_custom_extension)
        add_layout.addWidget(self.new_ext_input)
        add_layout.addWidget(btn_add_ext)
        layout.addLayout(add_layout)

        self.ext_badges = []
        self.populate_extension_badges()

    def _build_excludes_tab(self):
        layout = QVBoxLayout(self.tab_excludes)
        layout.addWidget(QLabel("Выберите папки для безусловного исключения из парсинга:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QFrame()
        self.exclude_grid_layout = QGridLayout(scroll_content)
        self.exclude_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        add_layout = QHBoxLayout()
        self.new_exclude_input = QLineEdit()
        self.new_exclude_input.setPlaceholderText("target, temp, logs, out...")
        btn_add_exclude = QPushButton("Игнорировать папку")
        btn_add_exclude.clicked.connect(self.add_custom_exclude)
        add_layout.addWidget(self.new_exclude_input)
        add_layout.addWidget(btn_add_exclude)
        layout.addLayout(add_layout)

        self.exclude_badges = []
        self.populate_exclude_badges()

    def _build_gitignore_tab(self):
        layout = QVBoxLayout(self.tab_gitignore)
        
        self.lbl_gitignore_info = QLabel()
        self.lbl_gitignore_info.setWordWrap(True)
        layout.addWidget(self.lbl_gitignore_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QFrame()
        self.gitignore_grid_layout = QGridLayout(scroll_content)
        self.gitignore_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        self.gitignore_badges = []
        self.populate_gitignore_badges()

    def populate_extension_badges(self):
        for b in self.ext_badges:
            b.deleteLater()
        self.ext_badges.clear()

        all_known = self.config_manager.get("all_known_extensions", [])
        active_exts = self.config_manager.get("active_extensions", [])

        cols = 4
        for idx, ext in enumerate(all_known):
            is_active = ext in active_exts
            badge = BadgeButton(ext, active=is_active)
            row = idx // cols
            col = idx % cols
            self.ext_grid_layout.addWidget(badge, row, col)
            self.ext_badges.append(badge)

    def populate_exclude_badges(self):
        for b in self.exclude_badges:
            b.deleteLater()
        self.exclude_badges.clear()

        all_known_excludes = self.config_manager.get("all_known_excludes", [])
        active_excludes = self.config_manager.get("global_excludes", [])

        cols = 3
        for idx, folder in enumerate(all_known_excludes):
            is_active = folder in active_excludes
            badge = BadgeButton(folder, active=is_active)
            row = idx // cols
            col = idx % cols
            self.exclude_grid_layout.addWidget(badge, row, col)
            self.exclude_badges.append(badge)

    def populate_gitignore_badges(self):
        """Парсит .gitignore открытого проекта и выводит его правила чипсами."""
        for b in self.gitignore_badges:
            b.deleteLater()
        self.gitignore_badges.clear()

        # Ищем путь к открытой папке проекта через родительское окно
        root_dir = ""
        if self.parent() and hasattr(self.parent(), "root_dir"):
            root_dir = self.parent().root_dir

        if not root_dir or not os.path.exists(root_dir):
            self.lbl_gitignore_info.setText("Проект не выбран. Откройте директорию проекта, чтобы увидеть его .gitignore.")
            return

        gitignore_path = os.path.join(root_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            self.lbl_gitignore_info.setText("Файл .gitignore в корне выбранного проекта не обнаружен.")
            return

        self.lbl_gitignore_info.setText(
            "Правила из .gitignore вашего проекта.\n"
            "🔵 Синий бадж — правило АКТИВНО (файлы скрыты).\n"
            "⚪ Серый бадж — правило ОТКЛЮЧЕНО (файлы будут принудительно добавлены в сканирование)."
        )

        # Парсим правила .gitignore
        from core.ignore_rules import parse_gitignore
        rules = parse_gitignore(gitignore_path)

        if not rules:
            self.lbl_gitignore_info.setText("Файл .gitignore найден, но он пуст.")
            return

        disabled_rules = self.config_manager.get("gitignore_disabled_rules", [])

        cols = 3
        for idx, rule in enumerate(rules):
            # Если правило отсутствует в списке отключенных -> оно активно (True)
            is_active = rule not in disabled_rules
            badge = BadgeButton(rule, active=is_active)
            row = idx // cols
            col = idx % cols
            self.gitignore_grid_layout.addWidget(badge, row, col)
            self.gitignore_badges.append(badge)

    def on_preset_selected(self, preset_name):
        presets_data = self.config_manager.get("presets", {})
        target_exts = presets_data.get(preset_name, [])

        for badge in self.ext_badges:
            is_active = (badge.item_text in target_exts) if preset_name != "Все текстовые файлы (без ограничений)" else False
            badge.setChecked(is_active)
            badge.active = is_active
            badge.update_style()

    def add_custom_extension(self):
        text = self.new_ext_input.text().strip().lower()
        if not text:
            return
        if not text.startswith('.'):
            text = '.' + text

        all_known = self.config_manager.get("all_known_extensions", [])
        if text in all_known:
            QMessageBox.information(self, "Инфо", f"Расширение {text} уже добавлено.")
            return

        all_known.append(text)
        self.config_manager.set("all_known_extensions", all_known)
        
        active_exts = self.config_manager.get("active_extensions", [])
        active_exts.append(text)
        self.config_manager.set("active_extensions", active_exts)

        self.populate_extension_badges()
        self.new_ext_input.clear()

    def add_custom_exclude(self):
        text = self.new_exclude_input.text().strip()
        if not text:
            return

        all_known_excludes = self.config_manager.get("all_known_excludes", [])
        if text in all_known_excludes:
            QMessageBox.information(self, "Инфо", f"Папка '{text}' уже занесена в базу.")
            return

        all_known_excludes.append(text)
        self.config_manager.set("all_known_excludes", all_known_excludes)

        active_excludes = self.config_manager.get("global_excludes", [])
        active_excludes.append(text)
        self.config_manager.set("global_excludes", active_excludes)

        self.populate_exclude_badges()
        self.new_exclude_input.clear()

    def trigger_parent_update(self):
        if self.parent() and hasattr(self.parent(), "check_for_updates_manual"):
            self.parent().check_for_updates_manual()

    def save_all_settings(self):
        """Сохраняет измененные вкладки настроек в локальный JSON."""
        # Сохранение общих настроек
        self.config_manager.set("use_gitignore", self.chk_gitignore.isChecked())
        self.config_manager.set("ignore_binary", self.chk_ignore_binary.isChecked())
        self.config_manager.set("ignore_lockfiles", self.chk_ignore_lockfiles.isChecked())
        self.config_manager.set("theme", self.combo_theme.currentText())
        self.config_manager.set("auto_check_updates", self.chk_auto_update.isChecked())

        # Сохранение активных расширений и текущего пресета
        active_exts = [b.item_text for b in self.ext_badges if b.active]
        self.config_manager.set("active_extensions", active_exts)
        self.config_manager.set("selected_preset", self.combo_presets.currentText())

        # Сохранение активных папок-исключений
        active_excludes = [b.item_text for b in self.exclude_badges if b.active]
        self.config_manager.set("global_excludes", active_excludes)

        # Сохранение правил .gitignore, которые юзер сделал неактивными (серыми)
        disabled_rules = [b.item_text for b in self.gitignore_badges if not b.active]
        self.config_manager.set("gitignore_disabled_rules", disabled_rules)

        self.accept()