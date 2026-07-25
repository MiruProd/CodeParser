from core.interfaces.transformer_step import ITransformerStep


class WhitespaceCompressorStep(ITransformerStep):

    def transform(self, text: str, ext: str) -> str:
        if not text:
            return text

        lines = text.splitlines()
        compressed_lines = []

        for line in lines:
            cleaned_line = line.rstrip()
            if not cleaned_line:
                continue
            compressed_lines.append(cleaned_line)

        return "\n".join(compressed_lines)