from core.interfaces.token_counter import ITokenCounter
from core.tokenizers.approximate_counter import ApproximateTokenCounter


class TokenCounterFactory:

    @staticmethod
    def create_counter(use_exact: bool = True, encoding_name: str = "cl100k_base") -> ITokenCounter:
        if use_exact:
            try:
                from core.tokenizers.tiktoken_counter import TiktokenCounter
                return TiktokenCounter(encoding_name=encoding_name)
            except Exception:
                pass
        return ApproximateTokenCounter()