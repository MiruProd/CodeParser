# src/ui/main_window.py

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QCheckBox, QTextEdit, 
    QTreeWidget, QTreeWidgetItem, QSplitter, QGroupBox, 
    QMessageBox, QStyle, QStatusBar, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from core.constants import PRESETS, UNIVERSAL_GLOBAL_EXCLUDES
from core.parser import scan_directory, build_payload
from ui.style import get_stylesheet, DARK_PALETTE, LIGHT_PALETTE


class PackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NextWG Smart Code Packer")
        self.resize(1150, 750)
        
        # Динамическая загрузка векторной иконки приложения
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icon.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Инициализируем тему оформления по умолчанию
        self.setStyleSheet(get_stylesheet(DARK_PALETTE))

        self.root_dir = ""
        self.root_node = None  # Ссылка на распарсенную модель дерева FileNode

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. Верхний блок выбора директорий
        paths_group = self._create_paths_group()
        main_layout.addWidget(paths_group)

        # 2. Средний блок со сплиттером
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        tree_container = self._create_tree_panel()
        right_panel = self._create_right_panel()
        
        splitter.addWidget(tree_container)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter, 1)

        # 3. Нижний блок с кнопками операций
        bottom_layout = self._create_bottom_panel()
        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе.")

    def _create_paths_group(self):
        group = QGroupBox("Директории и сохранение")
        layout = QVBoxLayout(group)

        # Обход исходной директории
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Папка проекта:"))
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Выберите корневую папку вашего проекта...")
        dir_layout.addWidget(self.dir_input)
        
        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_directory)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        # Выбор выходного TXT
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Файл сохранения (.txt):"))
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
        toolbar.addWidget(QLabel("Файлы для экспорта:"))
        
        btn_check_all = QPushButton("Выделить всё")
        btn_check_all.clicked.connect(lambda: self.check_all_items(True))
        toolbar.addWidget(btn_check_all)

        btn_uncheck_all = QPushButton("Снять выделение")
        btn_uncheck_all.clicked.connect(lambda: self.check_all_items(False))
        toolbar.addWidget(btn_uncheck_all)

        btn_expand = QPushButton("Развернуть всё")
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        toolbar.addWidget(btn_expand)

        btn_collapse = QPushButton("Свернуть всё")
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        toolbar.addWidget(btn_collapse)
        
        layout.addLayout(toolbar)

        # Дерево проекта на базе QTreeWidget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Структура папок и файлов", "Размер"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
        
        layout.addWidget(self.tree_widget)
        return container

    def _create_right_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        filter_group = QGroupBox("Параметры фильтрации")
        filter_layout = QVBoxLayout(filter_group)

        self.chk_gitignore = QCheckBox("Использовать правила .gitignore")
        self.chk_gitignore.setChecked(True)
        self.chk_gitignore.stateChanged.connect(self.reload_tree)
        filter_layout.addWidget(self.chk_gitignore)

        self.chk_ignore_binary = QCheckBox("Игнорировать бинарные файлы (картинки, архивы и др.)")
        self.chk_ignore_binary.setChecked(True)
        self.chk_ignore_binary.stateChanged.connect(self.reload_tree)
        filter_layout.addWidget(self.chk_ignore_binary)

        self.chk_ignore_lockfiles = QCheckBox("Игнорировать лок-файлы и автогенерацию")
        self.chk_ignore_lockfiles.setChecked(True)
        self.chk_ignore_lockfiles.stateChanged.connect(self.reload_tree)
        filter_layout.addWidget(self.chk_ignore_lockfiles)

        # Выбор расширений
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Пресет расширений:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItems(list(PRESETS.keys()))
        self.combo_presets.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.combo_presets)
        filter_layout.addLayout(preset_layout)

        # Ручные параметры исключений и белых списков
        filter_layout.addWidget(QLabel("Только расширения (через запятую):"))
        self.whitelist_input = QLineEdit()
        self.whitelist_input.setPlaceholderText("Оставьте пустым для отображения всех файлов")
        self.whitelist_input.editingFinished.connect(self.reload_tree)
        filter_layout.addWidget(self.whitelist_input)

        filter_layout.addWidget(QLabel("Глобальные папки-исключения:"))
        self.manual_input = QLineEdit(UNIVERSAL_GLOBAL_EXCLUDES)
        self.manual_input.editingFinished.connect(self.reload_tree)
        filter_layout.addWidget(self.manual_input)

        # Интегрированный переключатель тем
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема оформления:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Темная (VS Code)", "Светлая"])
        self.combo_theme.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.combo_theme)
        filter_layout.addLayout(theme_layout)

        layout.addWidget(filter_group)

        # Окно логирования операций
        log_group = QGroupBox("Лог работы")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        layout.addWidget(log_group, 1)
        return container

    def _create_bottom_panel(self):
        layout = QHBoxLayout()
        
        self.lbl_stats = QLabel("Выбрано файлов: 0 | Общий размер: 0 KB | Оценка токенов: ~0")
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

    # --- СЛОТЫ И КЛИЕНТСКАЯ ЛОГИКА ---

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.root_dir = os.path.abspath(directory)
            self.dir_input.setText(self.root_dir)
            self.out_input.setText(os.path.join(self.root_dir, "code_context.txt"))
            self.reload_tree()

    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.out_input.setText(file_path)

    def on_preset_changed(self, preset_name):
        extensions = PRESETS.get(preset_name, "")
        self.whitelist_input.setText(extensions)
        self.reload_tree()

    def on_theme_changed(self, theme_name):
        if "Темная" in theme_name:
            self.setStyleSheet(get_stylesheet(DARK_PALETTE))
        else:
            self.setStyleSheet(get_stylesheet(LIGHT_PALETTE))

    def reload_tree(self):
        if not self.root_dir or not os.path.exists(self.root_dir):
            return

        self.status_bar.showMessage("Сборка объектного дерева на диске...")
        
        # Сканируем диск, создавая чистую модель FileNode вне контекста Qt
        self.root_node = scan_directory(
            root_dir=self.root_dir,
            use_gitignore=self.chk_gitignore.isChecked(),
            ignore_binary=self.chk_ignore_binary.isChecked(),
            ignore_lockfiles=self.chk_ignore_lockfiles.isChecked(),
            whitelist_input_text=self.whitelist_input.text(),
            manual_input_text=self.manual_input.text()
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
        """Рекурсивно проецирует чистую модель FileNode на виджеты QTreeWidgetItem."""
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

    # --- РАБОТА С ИНТЕРАКТИВНЫМИ ЧЕКБОКСАМИ ---

    def on_tree_item_changed(self, item, column):
        if column != 0:
            return
            
        # Блокировка сигналов необходима во избежание бесконечного рекурсивного триггера
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

    # --- СБОРА КОНТЕКСТА И СТАТИСТИКИ ---

    def get_selected_files_info(self, item=None):
        """Сбор плоского списка метаданных только выбранных пользователем файлов."""
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
        
        # Эвристическая оценка: ~4 байта на один токен для UTF-8 кода на английском языке
        estimated_tokens = round(total_size / 4)
        
        self.lbl_stats.setText(
            f"Выбрано файлов: {len(selected_files)} | "
            f"Итоговый размер: {total_kb} KB | Токены (оценка): ~{estimated_tokens}"
        )

    def _generate_payload(self):
        selected_files = self.get_selected_files_info()
        
        # Составляем набор относительных путей для обрезки вывода дерева ASCII
        selected_paths = set()
        for f in selected_files:
            rel_path = f['rel_path']
            selected_paths.add(rel_path)
            
            # Вносим родительские папки в набор, иначе усеченное дерево не построится
            parts = rel_path.split('/')
            for i in range(1, len(parts)):
                selected_paths.add("/".join(parts[:i]))

        return build_payload(self.root_dir, self.root_node, selected_files, selected_paths)

    def copy_to_clipboard(self):
        payload = self._generate_payload()
        if not payload:
            return
        
        # Использование встроенного буфера обмена операционной системы
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