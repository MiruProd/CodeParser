# src/ui/main_window.py

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QTextEdit, 
    QTreeWidget, QTreeWidgetItem, QSplitter, QGroupBox, 
    QMessageBox, QStyle, QStatusBar, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction

from core.parser import scan_directory, build_payload
from ui.style import get_stylesheet, DARK_PALETTE, LIGHT_PALETTE

# Интеграция модулей управления
from core.config_manager import ConfigManager
from core.watcher import ProjectWatcher
from core.updater import UpdateCheckerThread, perform_self_update, CURRENT_VERSION
from ui.settings_dialog import SettingsDialog


class PackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загрузка менеджера настроек
        self.config_manager = ConfigManager()
        
        self.setWindowTitle(f"CodeParser — {CURRENT_VERSION}")
        self.resize(1100, 700)
        
        # Поддержка перетаскивания файлов
        self.setAcceptDrops(True)
        
        try:
            from ui.icon_data import ICON_BASE64
            import base64
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(ICON_BASE64))
            self.setWindowIcon(QIcon(pixmap))
        except Exception:
            pass
        
        # Установка темы на основе профиля настроек
        self.update_application_theme()

        self.root_dir = ""
        self.root_node = None

        # Фоновый наблюдатель изменений в файлах
        self.watcher = ProjectWatcher()
        self.watcher.file_changed.connect(self.on_file_changed_event)
        
        # Таймер подавления дребезга (debounce)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.reload_tree)

        self.init_ui()

        # Автопроверка обновлений
        if self.config_manager.get("auto_check_updates", True):
            self.check_for_updates(silent=True)

    def init_ui(self):
        # Создаем верхнее системное меню (MenuBar)
        self._create_menu_bar()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Информационная верхняя группа путей
        paths_group = self._create_paths_group()
        main_layout.addWidget(paths_group)

        # Сплиттер для дерева и логов
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        tree_container = self._create_tree_panel()
        log_container = self._create_log_panel()
        
        splitter.addWidget(tree_container)
        splitter.addWidget(log_container)
        splitter.setSizes([650, 450])
        
        main_layout.addWidget(splitter, 1)

        # Нижняя панель статистики и экспорта
        bottom_layout = self._create_bottom_panel()
        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе.")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # Меню Файл
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

        # Меню Настройки
        settings_menu = menu_bar.addMenu("Настройки")
        
        act_pref = QAction("⚙ Параметры...", self)
        act_pref.setShortcut("Ctrl+P")
        act_pref.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(act_pref)

        # Меню Справка
        help_menu = menu_bar.addMenu("Справка")
        
        act_check = QAction("Проверить обновления...", self)
        act_check.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(act_check)

        act_about = QAction("О программе", self)
        act_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(act_about)

    def _create_paths_group(self):
        group = QGroupBox("Папка проекта и экспорт")
        layout = QVBoxLayout(group)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Проект:"))
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Выберите проект через меню или перетащите папку сюда...")
        dir_layout.addWidget(self.dir_input)
        
        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_directory)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Экспорт:"))
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("Путь к итоговому .txt файлу контекста...")
        out_layout.addWidget(self.out_input)
        
        btn_browse_out = QPushButton("Выбрать...")
        btn_browse_out.clicked.connect(self.browse_output_file)
        out_layout.addWidget(btn_browse_out)
        layout.addLayout(out_layout)

        return group

    def _create_tree_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Структура для экспорта:"))
        
        btn_check_all = QPushButton("Выделить всё")
        btn_check_all.clicked.connect(lambda: self.check_all_items(True))
        toolbar.addWidget(btn_check_all)

        btn_uncheck_all = QPushButton("Снять выделение")
        btn_uncheck_all.clicked.connect(lambda: self.check_all_items(False))
        toolbar.addWidget(btn_uncheck_all)

        btn_expand = QPushButton("Развернуть")
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        toolbar.addWidget(btn_expand)

        btn_collapse = QPushButton("Свернуть")
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        toolbar.addWidget(btn_collapse)
        
        layout.addLayout(toolbar)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Файлы и каталоги", "Размер"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
        
        layout.addWidget(self.tree_widget)
        return container

    def _create_log_panel(self):
        container = QGroupBox("Лог работы")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        return container

    def _create_bottom_panel(self):
        layout = QHBoxLayout()
        
        self.lbl_stats = QLabel("Выбрано файлов: 0 | Общий размер: 0 KB | Токены (оценка): ~0")
        self.lbl_stats.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_stats, 1)

        self.btn_copy = QPushButton("Скопировать в буфер")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.btn_copy)

        self.btn_save = QPushButton("Записать в TXT")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_to_txt)
        layout.addWidget(self.btn_save)

        return layout

    def update_application_theme(self):
        theme = self.config_manager.get("theme", "Темная (VS Code)")
        if "Темная" in theme:
            self.setStyleSheet(get_stylesheet(DARK_PALETTE))
        else:
            self.setStyleSheet(get_stylesheet(LIGHT_PALETTE))

    # --- Обработка Drag & Drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.root_dir = os.path.abspath(path)
                self.dir_input.setText(self.root_dir)
                self.out_input.setText(os.path.join(self.root_dir, "code_context.txt"))
                
                # Запускаем наблюдение за изменениями
                self.watcher.start_watching(self.root_dir)
                self.reload_tree()
                break

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.root_dir = os.path.abspath(directory)
            self.dir_input.setText(self.root_dir)
            self.out_input.setText(os.path.join(self.root_dir, "code_context.txt"))
            
            self.watcher.start_watching(self.root_dir)
            self.reload_tree()

    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.out_input.setText(file_path)
            self.reload_tree()

    def on_file_changed_event(self):
        # Перезапуск сборки дерева с гашением дребезга (debounce)
        self.update_timer.start(1500)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.update_application_theme()
            self.reload_tree()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "О программе CodeParser",
            f"<b>CodeParser</b> — Версия {CURRENT_VERSION}<br><br>"
            "Утилита для быстрой подготовки контекста исходного кода "
            "для последующей отправки в LLM (ChatGPT, Claude, Gemini).<br><br>"
            "Разработано с использованием PyQt6 и watchdog."
        )

    def check_for_updates(self, silent=True):
        self.update_thread = UpdateCheckerThread(self)
        self.update_thread.check_finished.connect(
            lambda available, version, url: self.on_update_check_finished(available, version, url, silent)
        )
        self.update_thread.start()

    def check_for_updates_manual(self):
        self.status_bar.showMessage("Проверка обновлений...")
        self.check_for_updates(silent=False)

    def on_update_check_finished(self, available, version, url, silent):
        if available and url:
            reply = QMessageBox.question(
                self, 
                "Доступно обновление", 
                f"Найдена новая версия программы: {version}.\nЖелаете обновиться автоматически сейчас?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.status_bar.showMessage("Скачивание обновления...")
                success, error_msg = perform_self_update(url)
                if not success:
                    QMessageBox.warning(self, "Ошибка обновления", f"Не удалось выполнить обновление: {error_msg}")
                    self.status_bar.showMessage("Не удалось обновить приложение.")
        else:
            if not silent:
                QMessageBox.information(self, "Обновления", "У вас установлена последняя версия.")
                self.status_bar.showMessage("Версия актуальна.")

    def reload_tree(self):
        if not self.root_dir or not os.path.exists(self.root_dir):
            return

        self.status_bar.showMessage("Сборка объектного дерева на диске...")
        
        # Получаем параметры фильтрации напрямую из конфигурации JSON
        active_exts = self.config_manager.get("active_extensions", [])
        whitelist_text = ", ".join(active_exts)

        excludes_list = self.config_manager.get("global_excludes", [])
        manual_excludes_text = ", ".join(excludes_list)

        disabled_rules = self.config_manager.get("gitignore_disabled_rules", [])

        self.root_node = scan_directory(
            root_dir=self.root_dir,
            use_gitignore=self.config_manager.get("use_gitignore", True),
            ignore_binary=self.config_manager.get("ignore_binary", True),
            ignore_lockfiles=self.config_manager.get("ignore_lockfiles", True),
            whitelist_input_text=whitelist_text,
            manual_input_text=manual_excludes_text,
            output_file_path=self.out_input.text().strip(),
            gitignore_disabled_rules=disabled_rules
        )

        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()

        if self.root_node:
            root_item = QTreeWidgetItem(self.tree_widget)
            root_item.setText(0, self.root_node.name)
            root_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            root_item.setCheckState(0, Qt.CheckState.Checked)
            
            root_item.setData(0, Qt.ItemDataRole.UserRole, {
                'full_path': self.root_node.full_path,
                'rel_path': self.root_node.rel_path,
                'is_dir': True,
                'size': 0
            })
            
            self._populate_ui_tree(root_item, self.root_node)
            root_item.setExpanded(True)

        self.tree_widget.blockSignals(False)
        
        self.update_stats()
        self.btn_copy.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.status_bar.showMessage("Проект просканирован успешно.")
        self.log_output.append(f"Обновлено дерево для: {self.root_dir}")

    def _populate_ui_tree(self, parent_item, model_node):
        for child in model_node.children:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, child.name)
            item.setCheckState(0, Qt.CheckState.Checked)
            
            if child.is_dir:
                item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                self._populate_ui_tree(item, child)
            else:
                kb_size = round(child.size / 1024, 1)
                item.setText(1, f"{kb_size} KB")
                item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

            item.setData(0, Qt.ItemDataRole.UserRole, {
                'full_path': child.full_path,
                'rel_path': child.rel_path,
                'is_dir': child.is_dir,
                'size': child.size
            })

    def on_tree_item_changed(self, item, column):
        if column != 0:
            return
            
        self.tree_widget.blockSignals(True)
        state = item.checkState(0)
        self._update_children_state(item, state)
        self._update_parent_state(item)
        self.tree_widget.blockSignals(False)
        
        self.update_stats()

    def _update_children_state(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._update_children_state(child, state)

    def _update_parent_state(self, item):
        parent = item.parent()
        if not parent:
            return
        
        checked_count = 0
        unchecked_count = 0
        child_count = parent.childCount()
        
        for i in range(child_count):
            state = parent.child(i).checkState(0)
            if state == Qt.CheckState.Checked:
                checked_count += 1
            elif state == Qt.CheckState.Unchecked:
                unchecked_count += 1
                
        if checked_count == child_count:
            parent.setCheckState(0, Qt.CheckState.Checked)
        elif unchecked_count == child_count:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            
        self._update_parent_state(parent)

    def check_all_items(self, check=True):
        if self.tree_widget.topLevelItemCount() == 0:
            return
            
        self.tree_widget.blockSignals(True)
        root_item = self.tree_widget.topLevelItem(0)
        state = Qt.CheckState.Checked if check else Qt.CheckState.Unchecked
        root_item.setCheckState(0, state)
        self._update_children_state(root_item, state)
        self.tree_widget.blockSignals(False)
        self.update_stats()

    def get_selected_files_info(self, item=None):
        if item is None:
            if self.tree_widget.topLevelItemCount() == 0:
                return []
            item = self.tree_widget.topLevelItem(0)

        files = []
        state = item.checkState(0)
        
        if state == Qt.CheckState.Unchecked:
            return []

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and not data.get('is_dir', False) and state == Qt.CheckState.Checked:
            files.append(data)
        
        for i in range(item.childCount()):
            files.extend(self.get_selected_files_info(item.child(i)))
            
        return files

    def update_stats(self):
        selected_files = self.get_selected_files_info()
        total_size = sum(f['size'] for f in selected_files)
        total_kb = round(total_size / 1024, 1)
        
        estimated_tokens = round(total_size / 2.7)
        
        self.lbl_stats.setText(
            f"Выбрано файлов: {len(selected_files)} | "
            f"Итоговый размер: {total_kb} KB | Токены (оценка): ~{estimated_tokens}"
        )

    def _generate_payload(self):
        selected_files = self.get_selected_files_info()
        
        selected_paths = set()
        for f in selected_files:
            rel_path = f['rel_path']
            selected_paths.add(rel_path)
            
            parts = rel_path.split('/')
            for i in range(1, len(parts)):
                selected_paths.add("/".join(parts[:i]))

        return build_payload(self.root_dir, self.root_node, selected_files, selected_paths)

    def copy_to_clipboard(self):
        payload = self._generate_payload()
        if not payload:
            return
        
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(payload)
        
        self.status_bar.showMessage("Сборка завершена. Данные в буфере обмена!")
        self.log_output.append("Контекст успешно скопирован в буфер обмена.")

    def save_to_txt(self):
        out_path = self.out_input.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Ошибка", "Укажите путь для сохранения .txt файла.")
            return

        payload = self._generate_payload()
        if not payload:
            return

        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(payload)
            self.status_bar.showMessage(f"Файл сохранен: {os.path.basename(out_path)}")
            self.log_output.append(f"Файл успешно записан: {out_path}")
            QMessageBox.information(self, "Успешно", f"Файл сохранен:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось записать файл на диск:\n{e}")

    def closeEvent(self, event):
        self.watcher.stop_watching()
        event.accept()