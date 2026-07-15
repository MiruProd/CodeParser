# src/ui/widgets/paths_panel.py

import os
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtCore import pyqtSignal

class PathsPanel(QGroupBox):
    """
    Виджет для управления путями к папке проекта и файлу экспорта контекста.
    """
    project_dir_changed = pyqtSignal(str)
    export_path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Папка проекта и экспорт", parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Проект:"))
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Выберите проект через кнопку или перетащите папку в окно...")
        self.dir_input.textChanged.connect(self.project_dir_changed.emit)
        dir_layout.addWidget(self.dir_input)
        
        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_directory)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Экспорт:"))
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("Путь к итоговому .txt файлу контекста...")
        self.out_input.textChanged.connect(self.export_path_changed.emit)
        out_layout.addWidget(self.out_input)
        
        btn_browse_out = QPushButton("Выбрать...")
        btn_browse_out.clicked.connect(self.browse_output_file)
        out_layout.addWidget(btn_browse_out)
        layout.addLayout(out_layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.set_project_dir(os.path.abspath(directory))

    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.set_export_path(file_path)

    def get_project_dir(self) -> str:
        return self.dir_input.text().strip()

    def set_project_dir(self, path: str):
        self.dir_input.setText(path)

    def get_export_path(self) -> str:
        return self.out_input.text().strip()

    def set_export_path(self, path: str):
        self.out_input.setText(path)