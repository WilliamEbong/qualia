"""Frozen backend interface; outputs are validated at the AI schema adapter."""

from typing import Protocol


class ClassificationBackend(Protocol):
    name: str
    external: bool

    def available(self) -> bool: ...

    def classify(self, segments: list[dict], schema: dict, context: dict) -> dict:
        """Return {predictions, input_tokens, output_tokens, cli_version}; no store writes."""
        ...
