import re
from core.interfaces.transformer_step import ITransformerStep


class SecretSanitizerStep(ITransformerStep):

    SECRET_PATTERNS = [
        (r'sk-[a-zA-Z0-9T3BlbkFJ]{20,}', '[REDACTED_OPENAI_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
        (r'xox[b-aprs]-[a-zA-Z0-9]{10,}', '[REDACTED_SLACK_TOKEN]'),
        (r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY]'),
        (r'-----BEGIN (RSA|EC|PGP|PRIVATE) KEY-----[\s\S]*?-----END \1 KEY-----', '[REDACTED_PRIVATE_KEY]'),
        (r'(?i)(api[_-]?key|secret|password|bearer)\s*[:=]\s*["\']([^"\']{8,})["\']', r'\1: "[REDACTED_SECRET]"')
    ]

    def transform(self, text: str, ext: str) -> str:
        if not text:
            return text

        sanitized = text
        for pattern, replacement in self.SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)

        return sanitized