# src/ui/widgets/control_panel.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox, QGroupBox, QTextEdit
from PyQt6.QtCore import pyqtSignal

class ControlPanel(QWidget):
    """
    Панель для управления параметрами контекста ИИ, выбора скиллов-инструкций и вывода логов работы.
    """
    prompt_changed = pyqtSignal()
    settings_changed = pyqtSignal()
    add_prompt_clicked = pyqtSignal()
    edit_prompt_clicked = pyqtSignal()
    auto_watch_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        ai_group = QGroupBox("Параметры контекста и ИИ")
        ai_layout = QVBoxLayout(ai_group)

        prompt_selector_layout = QHBoxLayout()
        prompt_selector_layout.addWidget(QLabel("Шаблон задачи (Скилл):"))
        self.combo_prompts = QComboBox()
        self.combo_prompts.currentTextChanged.connect(lambda: self.prompt_changed.emit())
        prompt_selector_layout.addWidget(self.combo_prompts, 1)

        btn_add_prompt = QPushButton("➕ Добавить")
        btn_add_prompt.clicked.connect(self.add_prompt_clicked.emit)
        prompt_selector_layout.addWidget(btn_add_prompt)

        btn_edit_prompt = QPushButton("⚙ Изменить")
        btn_edit_prompt.clicked.connect(self.edit_prompt_clicked.emit)
        prompt_selector_layout.addWidget(btn_edit_prompt)
        ai_layout.addLayout(prompt_selector_layout)

        toggles_layout = QHBoxLayout()
        self.chk_xml = QCheckBox("Формат XML")
        self.chk_xml.stateChanged.connect(lambda: self.settings_changed.emit())
        
        self.chk_strip_comments = QCheckBox("Без комментариев")
        self.chk_strip_comments.stateChanged.connect(lambda: self.settings_changed.emit())

        self.chk_compress_whitespace = QCheckBox("Сжать код (минимизировать)")
        self.chk_compress_whitespace.stateChanged.connect(lambda: self.settings_changed.emit())

        self.chk_watch_changes = QCheckBox("Авто-слежение")
        self.chk_watch_changes.stateChanged.connect(lambda state: self.auto_watch_changed.emit(state == 2))

        toggles_layout.addWidget(self.chk_xml)
        toggles_layout.addWidget(self.chk_strip_comments)
        toggles_layout.addWidget(self.chk_compress_whitespace)
        toggles_layout.addWidget(self.chk_watch_changes)
        ai_layout.addLayout(toggles_layout)

        layout.addWidget(ai_group)

        log_group = QGroupBox("Лог работы")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        layout.addWidget(log_group, 1)

    def populate_prompts(self, prompts_dict, last_prompt_key):
        self.combo_prompts.blockSignals(True)
        self.combo_prompts.clear()
        for key, value in prompts_dict.items():
            self.combo_prompts.addItem(value["title"], key)
        
        index = self.combo_prompts.findData(last_prompt_key)
        if index >= 0:
            self.combo_prompts.setCurrentIndex(index)
        self.combo_prompts.blockSignals(False)

    def get_current_prompt_key(self) -> str:
        return self.combo_prompts.currentData()

    def get_fast_settings(self) -> tuple:
        return (
            self.chk_xml.isChecked(),
            self.chk_strip_comments.isChecked(),
            self.chk_compress_whitespace.isChecked(),
            self.chk_watch_changes.isChecked()
        )

    def set_fast_settings(self, xml_format, strip_comments, compress_whitespace, auto_watch):
        self.chk_xml.blockSignals(True)
        self.chk_strip_comments.blockSignals(True)
        self.chk_compress_whitespace.blockSignals(True)
        self.chk_watch_changes.blockSignals(True)

        self.chk_xml.setChecked(xml_format)
        self.chk_strip_comments.setChecked(strip_comments)
        self.chk_compress_whitespace.setChecked(compress_whitespace)
        self.chk_watch_changes.setChecked(auto_watch)

        self.chk_xml.blockSignals(False)
        self.chk_strip_comments.blockSignals(False)
        self.chk_compress_whitespace.blockSignals(False)
        self.chk_watch_changes.blockSignals(False)

    def append_log(self, text):
        self.log_output.append(text)

    def clear_log(self):
        self.log_output.clear()