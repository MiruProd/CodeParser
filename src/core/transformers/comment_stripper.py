import re
from core.interfaces.transformer_step import ITransformerStep


class CommentStripperStep(ITransformerStep):

    def __init__(self, comment_rules: dict):
        self._comment_rules = comment_rules or {}

    def transform(self, text: str, ext: str) -> str:
        if not text or not self._comment_rules:
            return text

        ext = ext.lower()
        rules = self._comment_rules.get("rules", {})

        try:
            for rule_name, rule_data in rules.items():
                if ext in rule_data.get("extensions", []):
                    if rule_name == "python_style":
                        hash_pattern = rule_data.get("hash_pattern")
                        doc_pattern = rule_data.get("docstring_pattern")

                        if hash_pattern:
                            def replace_python_hash(match):
                                if match.group(1):
                                    return match.group(1)
                                if match.group(2):
                                    return match.group(2)
                                comment = match.group(3)
                                if comment and comment.startswith('#!'):
                                    return comment
                                return ""
                            text = re.sub(hash_pattern, replace_python_hash, text, flags=re.MULTILINE)

                        if doc_pattern:
                            text = re.sub(doc_pattern, '', text, flags=re.MULTILINE)
                        return text
                    else:
                        pattern = rule_data.get("pattern")
                        if not pattern:
                            continue

                        def replace_standard(match):
                            if match.group(1):
                                return match.group(1)
                            if match.group(2):
                                return match.group(2)
                            return ""

                        return re.sub(pattern, replace_standard, text, flags=re.MULTILINE | re.DOTALL)
        except Exception as e:
            print(f"Error stripping comments for {ext}: {e}")

        return text