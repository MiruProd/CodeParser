# src/ui/workers/payload_worker.py

from PyQt6.QtCore import QThread, pyqtSignal
from core.parser import build_payload

class PayloadWorker(QThread):
    """
    Фоновый рабочий поток для сборки и трансформации контекста.
    Предотвращает зависание графического интерфейса при обработке больших объемов кода.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, root_dir, root_node, selected_files, selected_paths, config_manager, system_prompt, xml_format, always_send_full_tree, strip_comments, compress_whitespace):
        super().__init__()
        self.root_dir = root_dir
        self.root_node = root_node
        self.selected_files = selected_files
        self.selected_paths = selected_paths
        self.config_manager = config_manager
        self.system_prompt = system_prompt
        self.xml_format = xml_format
        self.always_send_full_tree = always_send_full_tree
        self.strip_comments = strip_comments
        self.compress_whitespace = compress_whitespace

    def run(self):
        try:
            payload = build_payload(
                self.root_dir,
                self.root_node,
                self.selected_files,
                self.selected_paths,
                comment_rules=self.config_manager.comment_rules,
                strip_comments=self.strip_comments,
                compress_whitespace=self.compress_whitespace,
                system_prompt=self.system_prompt,
                xml_format=self.xml_format,
                always_send_full_tree=self.always_send_full_tree
            )
            self.finished.emit(payload)
        except Exception as e:
            self.error.emit(str(e))