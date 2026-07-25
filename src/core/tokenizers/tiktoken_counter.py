import tiktoken
from core.interfaces.token_counter import ITokenCounter


class TiktokenCounter(ITokenCounter):

    def __init__(self, encoding_name: str = "cl100k_base"):
        self._encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text, disallowed_special=()))