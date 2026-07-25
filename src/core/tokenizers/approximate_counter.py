from core.interfaces.token_counter import ITokenCounter


class ApproximateTokenCounter(ITokenCounter):

    def __init__(self, chars_per_token: float = 3.3):
        self._chars_per_token = chars_per_token

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return round(len(text) / self._chars_per_token)