import re
from core.interfaces.transformer_step import ITransformerStep


class BraceLanguageSkeletonizerStep(ITransformerStep):

    SUPPORTED_EXTENSIONS = {
        ".js", ".jsx", ".ts", ".tsx", ".c", ".cpp", ".h", ".hpp",
        ".go", ".rs", ".java", ".cs", ".php"
    }

    def transform(self, text: str, ext: str) -> str:
        if not text or ext.lower() not in self.SUPPORTED_EXTENSIONS:
            return text

        try:
            pattern = r'(\b(?:async\s+|public\s+|private\s+|protected\s+|static\s+|fn\s+|func\s+|function\s+)*[a-zA-Z_][a-zA-Z0-9_<>,\s]*\([^)]*\)\s*(?:->\s*[\w\<\>\[\]]+)?\s*)\{[^{}]*\}'
            sanitized = re.sub(pattern, r'\1{ /* ... implementation ... */ }', text, flags=re.DOTALL)
            return sanitized
        except Exception:
            return text