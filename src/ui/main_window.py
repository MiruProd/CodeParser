# src/ui/main_window.py

import os
import time
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter, QMessageBox, QStatusBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from config.config_manager import ConfigManager
from config.prompt_manager import PromptManager
from core.updater import CURRENT_VERSION

# Импортируем модули кастомных виджетов и контроллера из новых папок пакетов
from ui.widgets import PathsPanel, TreePanel, ControlPanel, BottomPanel
from ui.controller import PackerController
from ui.settings_dialog import SettingsDialog
from ui.style import get_stylesheet, DARK_PALETTE, LIGHT_PALETTE


class PackerApp(QMainWindow):
    """
    Класс представления (View) главного окна.
    Отвечает исключительно за разметку, меню, диалоги и трансляцию Drag-and-Drop событий.
    """
    def __init__(self):
        super().__init__()
        
        # Модели данных
        self.config_manager = ConfigManager()
        self.prompt_manager = PromptManager(self.config_manager.config_dir, self.config_manager)
        
        self.root_dir = ""
        self.update_application_theme()
        self.setAcceptDrops(True)

        self.init_ui()

        # Создаем контроллер, который автоматически настроит все связи и загрузит данные
        self.controller = PackerController(self, self.config_manager, self.prompt_manager)

    def init_ui(self):
        self._create_menu_bar()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. Верхняя панель путей
        self.paths_panel = PathsPanel(self)
        main_layout.addWidget(self.paths_panel)

        # Сплиттер для дерева и настроек ИИ с логами
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 2. Панель дерева и 3. Панель ИИ/логов
        self.tree_panel = TreePanel(self)
        self.control_panel = ControlPanel(self)

        splitter.addWidget(self.tree_panel)
        splitter.addWidget(self.control_panel)
        splitter.setSizes([650, 450])
        
        main_layout.addWidget(splitter, 1)

        # 4. Нижняя панель статистики и действий
        self.bottom_panel = BottomPanel(self)
        main_layout.addWidget(self.bottom_panel)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе.")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        
        act_open = QAction("Открыть папку проекта...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.browse_directory)
        file_menu.addAction(act_open)

        act_save_path = QAction("Выбрать файл сохранения...", self)
        act_save_path.triggered.connect(self.browse_output_file)
        file_menu.addAction(act_save_path)

        file_menu.addSeparator()
        
        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        settings_menu = menu_bar.addMenu("Настройки")
        
        act_pref = QAction("⚙ Параметры...", self)
        act_pref.setShortcut("Ctrl+P")
        act_pref.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(act_pref)

        help_menu = menu_bar.addMenu("Справка")
        
        act_check = QAction("Проверить обновления...", self)
        act_check.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(act_check)

        act_about = QAction("О программе", self)
        act_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(act_about)

    def browse_directory(self):
        self.paths_panel.browse_directory()

    def browse_output_file(self):
        self.paths_panel.browse_output_file()

    def create_new_prompt(self):
        from ui.prompt_edit_dialog import PromptCreateDialog
        dialog = PromptCreateDialog(self.prompt_manager, self)
        if dialog.exec() == PromptCreateDialog.DialogCode.Accepted:
            data = dialog.get_data()
            new_key = f"user_prompt_{int(time.time())}"
            self.prompt_manager.prompts[new_key] = data
            self.prompt_manager.save_prompts()
            self.control_panel.append_log(f"Лог: Создан новый скилл '{data['title']}'.")
            self.config_manager.set("last_prompt_key", new_key)
            self.control_panel.populate_prompts(self.prompt_manager.prompts, new_key)

    def edit_current_prompt(self):
        current_key = self.control_panel.get_current_prompt_key()
        if not current_key:
            return
            
        prompt_data = self.prompt_manager.prompts[current_key]
        from ui.prompt_edit_dialog import PromptEditDialog
        dialog = PromptEditDialog(prompt_data["title"], prompt_data["prompt"], self)
        
        if dialog.exec() == PromptEditDialog.DialogCode.Accepted:
            new_text = dialog.get_text()
            self.prompt_manager.update_prompt(current_key, new_text)
            self.control_panel.append_log(f"Лог: Шаблон '{prompt_data['title']}' успешно обновлен.")
            self.controller.reload_tree()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.update_application_theme()
            self.controller.reload_tree()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "О программе CodeParser",
            "<b>CodeParser</b> — Версия " + CURRENT_VERSION + "<br><br>"
            "Утилита для быстрой подготовки контекста исходного кода "
            "для последующей отправки в LLM.<br><br>"
            "Разработано с использованием PyQt6 и watchdog."
        )

    def check_for_updates_manual(self):
        self.controller.check_for_updates(silent=False)

    def update_application_theme(self):
        theme = self.config_manager.get("theme", "Темная (VS Code)")
        if "Темная" in theme:
            self.setStyleSheet(get_stylesheet(DARK_PALETTE))
        else:
            self.setStyleSheet(get_stylesheet(LIGHT_PALETTE))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.paths_panel.set_project_dir(os.path.abspath(path))
                break

    def closeEvent(self, event):
        self.controller.watcher.stop_watching()
        event.accept()