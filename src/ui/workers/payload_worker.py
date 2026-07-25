from PyQt6.QtCore import QThread, pyqtSignal
from core.models.project_options import TransformOptions
from core.transformers.pipeline import TransformerPipeline
from core.transformers.comment_stripper import CommentStripperStep
from core.transformers.whitespace_compressor import WhitespaceCompressorStep
from core.transformers.secret_sanitizer import SecretSanitizerStep
from core.services.payload_service import PayloadService


class PayloadWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, root_dir, root_node, selected_files, selected_paths, config_manager, system_prompt, xml_format, always_send_full_tree, strip_comments, compress_whitespace, sanitize_secrets=False):
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
        self.sanitize_secrets = sanitize_secrets
        self.payload_service = PayloadService()

    def run(self):
        try:
            pipeline = TransformerPipeline()
            if self.strip_comments and self.config_manager.comment_rules:
                pipeline.add_step(CommentStripperStep(self.config_manager.comment_rules))
            if self.compress_whitespace:
                pipeline.add_step(WhitespaceCompressorStep())
            if self.sanitize_secrets:
                pipeline.add_step(SecretSanitizerStep())

            options = TransformOptions(
                strip_comments=self.strip_comments,
                compress_whitespace=self.compress_whitespace,
                sanitize_secrets=self.sanitize_secrets,
                xml_format=self.xml_format,
                always_send_full_tree=self.always_send_full_tree,
                system_prompt=self.system_prompt
            )

            payload = self.payload_service.build_payload(
                self.root_dir,
                self.root_node,
                self.selected_files,
                self.selected_paths,
                options,
                pipeline
            )
            self.finished.emit(payload)
        except Exception as e:
            self.error.emit(str(e))