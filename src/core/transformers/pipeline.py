from typing import List
from core.interfaces.transformer_step import ITransformerStep


class TransformerPipeline:

    def __init__(self, steps: List[ITransformerStep] = None):
        self._steps: List[ITransformerStep] = steps or []

    def add_step(self, step: ITransformerStep) -> "TransformerPipeline":
        self._steps.append(step)
        return self

    def execute(self, text: str, ext: str) -> str:
        current_text = text
        for step in self._steps:
            current_text = step.transform(current_text, ext)
        return current_text