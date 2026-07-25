from dataclasses import dataclass, field
from typing import List


@dataclass
class FileNode:
    name: str
    full_path: str
    rel_path: str
    is_dir: bool
    size: int = 0
    children: List["FileNode"] = field(default_factory=list)