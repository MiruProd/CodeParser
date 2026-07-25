import os
import sys
from PyQt6.QtWidgets import QMessageBox, QPushButton
from PyQt6.QtCore import QObject, QTimer

from core.models.project_options import ScanOptions
from core.services.scanner_service import ScannerService
from core.services.git_service import GitService
from core.services.dependency_service import DependencyService
from core.tokenizers.token_factory import TokenCounterFactory
from core.watcher import ProjectWatcher
from core.updater import UpdateCheckerThread, perform_self_update, apply_restart_and_exit
from ui.workers import PayloadWorker


class PackerController(QObject):

    def __init__(self, main_window, config_manager, prompt_manager):
        super().__init__(main_window)
        self.view = main_window
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager

        self.root_node = None
        self.payload_worker = None
        self.update_thread = None

        self.scanner_service = ScannerService()
        self.git_service = GitService()
        self.dependency_service = DependencyService()
        self.token_counter = TokenCounterFactory.create_counter(use_exact=True)

        self.watcher = ProjectWatcher()
        self.watcher.file_changed.connect(self.on_file_changed_event)

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.reload_tree)

        self._connect_signals()
        self._init_view_data()

    def _connect_signals(self):
        self.view.paths_panel.project_dir_changed.connect(self.on_project_dir_changed)
        self.view.paths_panel.export_path_changed.connect(self.on_export_path_changed)

        self.view.tree_panel.selection_changed.connect(self.update_stats)
        self.view.tree_panel.refresh_requested.connect(self.reload_tree)

        for btn in self.view.tree_panel.findChildren(QPushButton):
            if btn.text() == "Только Git":
                btn.clicked.connect(self.on_git_select_requested)
            elif btn.text() == "Импорты":
                btn.clicked.connect(self.on_deps_select_requested)

        self.view.control_panel.prompt_changed.connect(self.on_prompt_changed)
        self.view.control_panel.settings_changed.connect(self.on_fast_settings_changed)
        self.view.control_panel.auto_watch_changed.connect(self.on_auto_watch_changed)

        self.view.bottom_panel.copy_clicked.connect(self.copy_to_clipboard)
        self.view.bottom_panel.save_clicked.connect(self.save_to_txt)

    def _init_view_data(self):
        self.view.paths_panel.set_project_dir(self.view.root_dir)
        self.view.paths_panel.set_export_path(
            os.path.join(self.view.root_dir, "code_context.txt") if self.view.root_dir else ""
        )

        self.view.control_panel.populate_prompts(
            self.prompt_manager.prompts,
            self.config_manager.get("last_prompt_key", "just_code")
        )

        self.view.control_panel.set_fast_settings(
            self.config_manager.get("xml_format", True),
            self.config_manager.get("strip_comments", False),
            self.config_manager.get("compress_whitespace", False),
            self.config_manager.get("sanitize_secrets", False),
            self.config_manager.get("skeleton_mode", False),
            self.config_manager.get("auto_watch", True)
        )

    def on_project_dir_changed(self, path):
        self.view.root_dir = path
        self.view.paths_panel.set_export_path(
            os.path.join(self.view.root_dir, "code_context.txt") if self.view.root_dir else ""
        )

        xml, strip, compress, sanitize, skeleton, auto_watch = self.view.control_panel.get_fast_settings()
        if auto_watch and self.view.root_dir and os.path.exists(self.view.root_dir):
            self.watcher.start_watching(self.view.root_dir)
        else:
            self.watcher.stop_watching()

        self.reload_tree()

    def on_export_path_changed(self, path):
        self.reload_tree()

    def on_prompt_changed(self):
        current_key = self.view.control_panel.get_current_prompt_key()
        if current_key:
            self.config_manager.set("last_prompt_key", current_key)
            self.reload_tree()

    def on_fast_settings_changed(self):
        xml, strip, compress, sanitize, skeleton, auto_watch = self.view.control_panel.get_fast_settings()
        self.config_manager.set("xml_format", xml)
        self.config_manager.set("strip_comments", strip)
        self.config_manager.set("compress_whitespace", compress)
        self.config_manager.set("sanitize_secrets", sanitize)
        self.config_manager.set("skeleton_mode", skeleton)
        self.reload_tree()

    def on_auto_watch_changed(self, enabled):
        self.config_manager.set("auto_watch", enabled)
        if enabled:
            project_dir = self.view.paths_panel.get_project_dir()
            if project_dir and os.path.exists(project_dir):
                self.watcher.start_watching(project_dir)
                self.view.control_panel.append_log("Лог: Автоматическое слежение за папкой включено.")
        else:
            self.watcher.stop_watching()
            self.view.control_panel.append_log("Лог: Автоматическое слежение за папкой отключено.")

    def on_git_select_requested(self):
        project_dir = self.view.paths_panel.get_project_dir()
        success, msg, modified_files = self.git_service.get_modified_files(project_dir)
        if success:
            self.view.tree_panel.check_all_items(False)
            self.view.tree_panel.select_specific_paths(modified_files)
            self.view.status_bar.showMessage(msg)
            self.view.control_panel.append_log(f"Лог: {msg}")
        else:
            QMessageBox.warning(self.view, "Git Status", msg)

    def on_deps_select_requested(self):
        project_dir = self.view.paths_panel.get_project_dir()
        target_rel = self.view.tree_panel.get_current_focused_rel_path()
        if not target_rel:
            QMessageBox.information(self.view, "Импорты", "Выберите файл в дереве для анализа его импортов.")
            return

        deps = self.dependency_service.trace_dependencies(project_dir, target_rel)
        if not deps:
            QMessageBox.information(self.view, "Импорты", f"Для файла '{target_rel}' не найдено локальных импортов.")
            return

        self.view.tree_panel.select_specific_paths(deps)
        msg = f"Выделено импортируемых файлов ({len(deps)}) для '{target_rel}'"
        self.view.status_bar.showMessage(msg)
        self.view.control_panel.append_log(f"Лог: {msg}")

    def on_file_changed_event(self):
        self.update_timer.start(1500)

    def reload_tree(self):
        project_dir = self.view.paths_panel.get_project_dir()
        if not project_dir or not os.path.exists(project_dir):
            return

        self.view.status_bar.showMessage("Сборка объектного дерева на диске...")

        options = ScanOptions(
            use_gitignore=self.config_manager.get("use_gitignore", True),
            ignore_binary=self.config_manager.get("ignore_binary", True),
            ignore_lockfiles=self.config_manager.get("ignore_lockfiles", True),
            whitelist_extensions=self.config_manager.get("active_extensions", []),
            manual_excludes=self.config_manager.get("global_excludes", []),
            output_file_path=self.view.paths_panel.get_export_path(),
            gitignore_disabled_rules=self.config_manager.get("gitignore_disabled_rules", []),
            binary_extensions=self.config_manager.get("binary_extensions", []),
            lockfiles_excludes=self.config_manager.get("lockfiles_excludes", [])
        )

        saved_states = self.view.tree_panel.get_check_states()
        self.root_node = self.scanner_service.scan(project_dir, options)

        self.view.tree_panel.populate_tree(self.root_node, saved_states)
        self.update_stats()
        self.view.bottom_panel.set_actions_enabled(True)
        self.view.status_bar.showMessage("Проект просканирован успешно.")
        self.view.control_panel.append_log(f"Обновлено дерево для: {project_dir}")

    def update_stats(self):
        selected_files = self.view.tree_panel.get_selected_files_info()
        total_size = sum(f['size'] for f in selected_files)
        total_kb = round(total_size / 1024, 1)

        estimated_tokens = self.token_counter.count_tokens("a" * total_size)
        self.view.bottom_panel.update_stats(len(selected_files), total_kb, estimated_tokens)

    def start_payload_generation(self, callback_after_generation):
        if self.payload_worker and self.payload_worker.isRunning():
            return

        selected_files = self.view.tree_panel.get_selected_files_info()
        selected_paths = set()
        for f in selected_files:
            rel_path = f['rel_path']
            selected_paths.add(rel_path)
            parts = rel_path.split('/')
            for i in range(1, len(parts)):
                selected_paths.add("/".join(parts[:i]))

        current_key = self.view.control_panel.get_current_prompt_key()
        system_prompt = ""
        if current_key and current_key in self.prompt_manager.prompts:
            system_prompt = self.prompt_manager.prompts[current_key]["prompt"]

        xml_format, strip_comments, compress_whitespace, sanitize_secrets, skeleton_mode, auto_watch = self.view.control_panel.get_fast_settings()

        self.config_manager.set("xml_format", xml_format)
        self.config_manager.set("strip_comments", strip_comments)
        self.config_manager.set("compress_whitespace", compress_whitespace)
        self.config_manager.set("sanitize_secrets", sanitize_secrets)
        self.config_manager.set("skeleton_mode", skeleton_mode)

        always_send_full_tree = self.config_manager.get("always_send_full_tree", True)

        self.view.bottom_panel.set_actions_enabled(False)
        self.view.status_bar.showMessage("Сборка контекста в фоновом режиме...")

        self.payload_worker = PayloadWorker(
            self.view.paths_panel.get_project_dir(),
            self.root_node,
            selected_files,
            selected_paths,
            self.config_manager,
            system_prompt,
            xml_format,
            always_send_full_tree,
            strip_comments,
            compress_whitespace,
            sanitize_secrets,
            skeleton_mode
        )
        self.payload_worker.finished.connect(lambda payload: self.on_payload_generated(payload, callback_after_generation))
        self.payload_worker.error.connect(self.on_payload_error)
        self.payload_worker.start()

    def on_payload_generated(self, payload, callback):
        self.view.bottom_panel.set_actions_enabled(True)
        self.view.status_bar.showMessage("Сборка завершена успешно.")
        callback(payload)

    def on_payload_error(self, err_msg):
        self.view.bottom_panel.set_actions_enabled(True)
        self.view.status_bar.showMessage("Ошибка генерации.")
        QMessageBox.critical(self.view, "Ошибка генерации", f"Не удалось собрать контекст:\n{err_msg}")

    def copy_to_clipboard(self):
        self.start_payload_generation(self._copy_payload_action)

    def _copy_payload_action(self, payload):
        if not payload:
            return
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(payload)
        self.view.status_bar.showMessage("Данные скопированы в буфер обмена!")
        self.view.control_panel.append_log("Контекст успешно скопирован в буфер обмена.")

    def save_to_txt(self):
        out_path = self.view.paths_panel.get_export_path()
        if not out_path:
            QMessageBox.warning(self.view, "Ошибка", "Укажите путь для сохранения .txt файла.")
            return
        self.start_payload_generation(lambda payload: self._save_payload_action(payload, out_path))

    def _save_payload_action(self, payload, out_path):
        if not payload:
            return
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(payload)
            self.view.status_bar.showMessage(f"Файл сохранен: {os.path.basename(out_path)}")
            self.view.control_panel.append_log(f"Файл успешно записан: {out_path}")
            QMessageBox.information(self.view, "Успешно", f"Файл сохранен:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "Ошибка", f"Не удалось записать файл на диск:\n{e}")

    def check_for_updates(self, silent=True):
        self.update_thread = UpdateCheckerThread(self)
        self.update_thread.check_finished.connect(
            lambda available, version, url: self.on_update_check_finished(available, version, url, silent)
        )
        self.update_thread.start()

    def on_update_check_finished(self, available, version, url, silent):
        if available and url:
            reply = QMessageBox.question(
                self.view,
                "Доступно обновление",
                f"Найдена новая версия программы: {version}.\nЖелаете обновиться автоматически сейчас?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.view.status_bar.showMessage("Скачивание обновления...")
                success, msg, new_file_path = perform_self_update(url)
                if success:
                    QMessageBox.information(
                        self.view,
                        "Обновление готово",
                        f"{msg}\n\nПрограмма будет автоматически закрыта и перезапущена для завершения установки."
                    )
                    apply_restart_and_exit(new_file_path)
                else:
                    QMessageBox.warning(self.view, "Ошибка обновления", f"Не удалось выполнить обновление:\n{msg}")
                    self.view.status_bar.showMessage("Не удалось обновить приложение.")
        else:
            if not silent:
                QMessageBox.information(self.view, "Обновления", "У вас установлена последняя версия.")
                self.view.status_bar.showMessage("Версия актуальна.")