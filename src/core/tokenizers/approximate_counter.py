from core.interfaces.token_counter import ITokenCounter


class ApproximateTokenCounter(ITokenCounter):

    def __init__(self, chars_per_token: float = 2.7):
        self._chars_per_token = chars_per_token

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return round(len(text.encode("utf-8")) / self._chars_per_token)