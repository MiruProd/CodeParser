# src/ui/widgets/tree_panel.py

import os
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QStyle
from PyQt6.QtCore import Qt, pyqtSignal

class TreePanel(QWidget):
    """
    Интерактивная панель со структурой проекта, строкой поиска и инструментами выделения.
    """
    selection_changed = pyqtSignal()
    refresh_requested = pyqtSignal()
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Структура для экспорта:"))
        
        btn_check_all = QPushButton("Выделить всё")
        btn_check_all.clicked.connect(lambda: self.check_all_items(True))
        toolbar.addWidget(btn_check_all)

        btn_uncheck_all = QPushButton("Снять выделение")
        btn_uncheck_all.clicked.connect(lambda: self.check_all_items(False))
        toolbar.addWidget(btn_uncheck_all)

        btn_git_select = QPushButton("Только Git")
        btn_git_select.clicked.connect(self._on_git_select_clicked)
        toolbar.addWidget(btn_git_select)

        btn_expand = QPushButton("Развернуть")
        btn_expand.clicked.connect(lambda: self.tree_widget.expandAll())
        toolbar.addWidget(btn_expand)

        btn_collapse = QPushButton("Свернуть")
        btn_collapse.clicked.connect(lambda: self.tree_widget.collapseAll())
        toolbar.addWidget(btn_collapse)

        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Быстрый поиск файлов по имени или расширению...")
        self.search_input.textChanged.connect(self.filter_tree)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Файлы и каталоги", "Размер"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.itemChanged.connect(self._on_item_changed)
        
        layout.addWidget(self.tree_widget)

    def _on_item_changed(self, item, column):
        if column != 0:
            return
        self.tree_widget.blockSignals(True)
        state = item.checkState(0)
        self._update_children_state(item, state)
        self._update_parent_state(item)
        self.tree_widget.blockSignals(False)
        self.selection_changed.emit()

    def _on_git_select_clicked(self):
        # Будет обработано в контроллере главного окна, так как нужен путь root_dir
        pass

    def check_all_items(self, check=True):
        if self.tree_widget.topLevelItemCount() == 0:
            return
        self.tree_widget.blockSignals(True)
        root_item = self.tree_widget.topLevelItem(0)
        state = Qt.CheckState.Checked if check else Qt.CheckState.Unchecked
        root_item.setCheckState(0, state)
        self._update_children_state(root_item, state)
        self.tree_widget.blockSignals(False)
        self.selection_changed.emit()

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

    def get_check_states(self) -> dict:
        states = {}
        if self.tree_widget.topLevelItemCount() == 0:
            return states
        root_item = self.tree_widget.topLevelItem(0)
        self._collect_states(root_item, states)
        return states

    def _collect_states(self, item, states):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            rel_path = data.get('rel_path', '')
            states[rel_path] = item.checkState(0)
        for i in range(item.childCount()):
            self._collect_states(item.child(i), states)

    def get_selected_files_info(self, item=None) -> list:
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

    def populate_tree(self, root_node, saved_states=None):
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        if not root_node:
            self.tree_widget.blockSignals(False)
            return

        root_item = QTreeWidgetItem(self.tree_widget)
        root_item.setText(0, root_node.name)
        root_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        
        root_state = Qt.CheckState.Checked
        if saved_states and root_node.rel_path in saved_states:
            root_state = saved_states[root_node.rel_path]
        root_item.setCheckState(0, root_state)
        
        root_item.setData(0, Qt.ItemDataRole.UserRole, {
            'full_path': root_node.full_path,
            'rel_path': root_node.rel_path,
            'is_dir': True,
            'size': 0
        })
        
        self._populate_ui_tree(root_item, root_node, saved_states)
        root_item.setExpanded(True)
        self.tree_widget.blockSignals(False)

        if self.search_input.text().strip():
            self.filter_tree(self.search_input.text())

    def _populate_ui_tree(self, parent_item, model_node, saved_states=None):
        if saved_states is None:
            saved_states = {}

        for child in model_node.children:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, child.name)
            
            state = Qt.CheckState.Checked
            if child.rel_path in saved_states:
                state = saved_states[child.rel_path]
            item.setCheckState(0, state)
            
            if child.is_dir:
                item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                self._populate_ui_tree(item, child, saved_states)
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

    def filter_tree(self, text):
        text = text.lower().strip()
        if self.tree_widget.topLevelItemCount() == 0:
            return
        
        self.tree_widget.blockSignals(True)
        root_item = self.tree_widget.topLevelItem(0)
        self._filter_item_recursive(root_item, text)
        self.tree_widget.blockSignals(False)

    def _filter_item_recursive(self, item, text) -> bool:
        item_text = item.text(0).lower()
        match_self = text in item_text

        any_child_visible = False
        for i in range(item.childCount()):
            child_visible = self._filter_item_recursive(item.child(i), text)
            if child_visible:
                any_child_visible = True

        is_visible = match_self or any_child_visible
        item.setHidden(not is_visible)
        
        if text and any_child_visible:
            item.setExpanded(True)
            
        return is_visible

    def select_git_modified(self, root_dir) -> tuple:
        if not root_dir or not os.path.exists(root_dir):
            return False, "Папка проекта не найдена."
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            modified_files = set()
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    path_part = line[3:].strip()
                    if " -> " in path_part:
                        path_part = path_part.split(" -> ")[-1].strip()
                    path_part = path_part.strip('"\'')
                    normalized_path = path_part.replace('\\', '/')
                    modified_files.add(normalized_path)
            
            if not modified_files:
                return False, "Нет измененных файлов в репозитории Git."

            self.check_all_items(False)
            
            self.tree_widget.blockSignals(True)
            root_item = self.tree_widget.topLevelItem(0)
            self._check_git_items_recursive(root_item, modified_files)
            self.tree_widget.blockSignals(False)
            self.selection_changed.emit()
            return True, f"Успешно выделено файлов Git: {len(modified_files)}"
        except Exception as e:
            return False, f"Ошибка выполнения Git команды: {e}"

    def _check_git_items_recursive(self, item, modified_files):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            rel_path = data.get('rel_path', '')
            is_dir = data.get('is_dir', False)
            
            if not is_dir:
                if rel_path in modified_files:
                    item.setCheckState(0, Qt.CheckState.Checked)
                    self._update_parent_state(item)
            
        for i in range(item.childCount()):
            self._check_git_items_recursive(item.child(i), modified_files)