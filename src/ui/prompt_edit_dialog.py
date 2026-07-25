from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QLineEdit, QMessageBox,
    QTabWidget, QScrollArea, QFrame, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from config.resource_helper import get_resource_path


class PromptEditDialog(QDialog):

    def __init__(self, title, initial_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Редактирование: {title}")
        self.setMinimumSize(500, 350)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Текст системной инструкции для ИИ-ассистента:"))

        self.editor = QTextEdit()
        self.editor.setPlainText(initial_text)
        layout.addWidget(self.editor, 1)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить изменения")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_text(self) -> str:
        return self.editor.toPlainText()


class RuleCardWidget(QFrame):

    def __init__(self, rule_data, on_edit_callback, on_delete_callback, parent=None):
        super().__init__(parent)
        self.rule_data = rule_data
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("RuleCardWidget { margin: 2px; padding: 2px; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.chk_active = QCheckBox()
        self.chk_active.setChecked(self.rule_data.get("active", False))
        self.chk_active.stateChanged.connect(self.on_checkbox_toggled)
        layout.addWidget(self.chk_active)

        text_layout = QVBoxLayout()
        self.lbl_title = QLabel(self.rule_data.get("title", ""))
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 11px;")

        self.lbl_desc = QLabel(self.rule_data.get("description", ""))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #71717a; font-size: 10px;")

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)
        layout.addLayout(text_layout, 1)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(QIcon(get_resource_path("resources/icons/edit.svg")))
        self.btn_edit.setToolTip("Редактировать текст инструкции ИИ")
        self.btn_edit.setFixedWidth(28)
        self.btn_edit.clicked.connect(lambda: self.on_edit_callback(self.rule_data))

        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(QIcon(get_resource_path("resources/icons/delete.svg")))
        self.btn_delete.setToolTip("Удалить правило")
        self.btn_delete.setFixedWidth(28)
        self.btn_delete.clicked.connect(lambda: self.on_delete_callback(self.rule_data))

        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

    def on_checkbox_toggled(self, state):
        self.rule_data["active"] = (state == Qt.CheckState.Checked.value)


class CustomRuleAddDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить новое правило")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Заголовок правила для человека:"))
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Например: Отступы в JSON")
        layout.addWidget(self.txt_title)

        layout.addWidget(QLabel("Краткое описание (что оно делает):"))
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Указывает ИИ форматировать JSON с отступом в 2 пробела...")
        layout.addWidget(self.txt_desc)

        layout.addWidget(QLabel("Техническая инструкция для ИИ (Rule Text):"))
        self.txt_rule = QTextEdit()
        self.txt_rule.setPlaceholderText("Format all output JSON blocks strictly with 2 spaces indentation...")
        layout.addWidget(self.txt_rule, 1)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.validate_and_accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.txt_title.text().strip() or not self.txt_rule.toPlainText().strip():
            QMessageBox.warning(self, "Ошибка", "Заголовок и текст инструкции для ИИ не могут быть пустыми.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "title": self.txt_title.text().strip(),
            "description": self.txt_desc.text().strip(),
            "rule_text": self.txt_rule.toPlainText().strip()
        }


class PromptCreateDialog(QDialog):

    def __init__(self, prompt_manager, parent=None):
        super().__init__(parent)
        self.prompt_manager = prompt_manager
        self.setWindowTitle("Конструктор скиллов ИИ")
        self.setMinimumSize(600, 500)

        self.categories = {
            "system_role": "Роль ИИ",
            "interaction_protocol": "Протокол диалога",
            "quality_standards": "Стандарты качества",
            "version_alignment": "Синхронизация версий"
        }

        self.scroll_layouts = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Название нового скилла:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: Python Senior Architect")
        title_layout.addWidget(self.title_input, 1)
        main_layout.addLayout(title_layout)

        self.tab_widget = QTabWidget()
        for cat_key, cat_title in self.categories.items():
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_content = QFrame()

            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            scroll_layout.setSpacing(4)
            scroll_layout.setContentsMargins(4, 4, 4, 4)

            scroll.setWidget(scroll_content)
            tab_layout.addWidget(scroll, 1)

            btn_add_rule = QPushButton(" Добавить свое правило")
            btn_add_rule.setIcon(QIcon(get_resource_path("resources/icons/add.svg")))
            btn_add_rule.clicked.connect(lambda checked, ck=cat_key: self.create_custom_rule(ck))
            tab_layout.addWidget(btn_add_rule)

            self.tab_widget.addTab(tab_widget, cat_title)
            self.scroll_layouts[cat_key] = scroll_layout

        main_layout.addWidget(self.tab_widget, 1)

        bottom_layout = QHBoxLayout()
        btn_compile = QPushButton("Собрать и сохранить скилл")
        btn_compile.clicked.connect(self.compile_and_save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_compile)
        bottom_layout.addWidget(btn_cancel)
        main_layout.addLayout(bottom_layout)

        self.render_all_cards()

    def render_all_cards(self):
        for cat_key, layout in self.scroll_layouts.items():
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            category_rules = self.prompt_manager.rules.get(cat_key, [])
            for rule in category_rules:
                card = RuleCardWidget(
                    rule_data=rule,
                    on_edit_callback=self.on_edit_rule,
                    on_delete_callback=self.on_delete_rule,
                    parent=self
                )
                layout.addWidget(card)

    def create_custom_rule(self, category_key):
        dialog = CustomRuleAddDialog(self)
        if dialog.exec() == CustomRuleAddDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.prompt_manager.add_custom_rule(
                category=category_key,
                title=data["title"],
                description=data["description"],
                rule_text=data["rule_text"]
            )
            self.render_all_cards()

    def on_edit_rule(self, rule_data):
        dialog = PromptEditDialog(rule_data["title"], rule_data["rule_text"], self)
        if dialog.exec() == PromptEditDialog.DialogCode.Accepted:
            rule_data["rule_text"] = dialog.get_text()
            self.prompt_manager.save_rules()
            self.render_all_cards()

    def on_delete_rule(self, rule_data):
        reply = QMessageBox.question(
            self, "Удаление правила",
            f"Вы уверены, что хотите безвозвратно удалить правило '{rule_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for cat_key, rules_list in self.prompt_manager.rules.items():
                if rule_data in rules_list:
                    rules_list.remove(rule_data)
                    break
            self.prompt_manager.save_rules()
            self.render_all_cards()

    def compile_and_save(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Укажите название собираемого скилла.")
            return

        active_rules_by_category = {}
        for cat_key, rules_list in self.prompt_manager.rules.items():
            active_texts = [r["rule_text"] for r in rules_list if r.get("active", False)]
            if active_texts:
                active_rules_by_category[cat_key] = active_texts

        self.compiled_prompt_text = self.prompt_manager.compile_prompt(active_rules_by_category)
        self.prompt_manager.save_rules()
        self.accept()

    def get_data(self) -> dict:
        return {
            "title": self.title_input.text().strip(),
            "prompt": self.compiled_prompt_text,
            "custom": True
        }