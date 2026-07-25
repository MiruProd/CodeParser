from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScanOptions:
    use_gitignore: bool = True
    ignore_binary: bool = True
    ignore_lockfiles: bool = True
    whitelist_extensions: List[str] = field(default_factory=list)
    manual_excludes: List[str] = field(default_factory=list)
    output_file_path: Optional[str] = None
    gitignore_disabled_rules: List[str] = field(default_factory=list)
    binary_extensions: List[str] = field(default_factory=list)
    lockfiles_excludes: List[str] = field(default_factory=list)


@dataclass
class TransformOptions:
    strip_comments: bool = False
    compress_whitespace: bool = False
    sanitize_secrets: bool = False
    skeleton_mode: bool = False
    xml_format: bool = True
    always_send_full_tree: bool = True
    system_prompt: str = ""