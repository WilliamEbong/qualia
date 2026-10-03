"""Immutable domain values; all offsets are Unicode code-point indices."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def __post_init__(self):
        if self.start < 0 or self.end <= self.start:
            raise ValueError('span must have a nonnegative start and a greater end')
