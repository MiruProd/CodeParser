import re
from core.interfaces.transformer_step import ITransformerStep


class SecretSanitizerStep(ITransformerStep):

    SECRET_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_OPENAI_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
        (r'xox[b-aprs]-[a-zA-Z0-9]{10,}', '[REDACTED_SLACK_TOKEN]'),
        (r'\bAKIA[0-9A-Z]{16}\b', '[REDACTED_AWS_KEY]'),
        (r'-----BEGIN [A-Z ]+ PRIVATE KEY-----[\r\n][\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----', '[REDACTED_PRIVATE_KEY]'),
        (r'(?i)^(\s*(?:[\w_.]*?(?:api[_-]?key|secret|password|token|bearer)[\w_.]*?)\s*[:=]\s*)(["\'])(?:(?!\2).){8,}\2', r'\1\2[REDACTED_SECRET]\2')
    ]

    def transform(self, text: str, ext: str) -> str:
        if not text:
            return text

        sanitized = text
        for pattern, replacement in self.SECRET_PATTERNS:
            try:
                if pattern.startswith('(?i)^'):
                    sanitized = re.sub(pattern, replacement, sanitized, flags=re.MULTILINE)
                else:
                    sanitized = re.sub(pattern, replacement, sanitized)
            except Exception:
                pass

        return sanitized