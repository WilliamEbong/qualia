"""Deterministic text spans; offsets always index the unchanged Python string."""

import re


def segment_text(text: str, method: str = 'paragraph', speaker: str | None = None) -> list[dict]:
    """Split blank-line paragraphs, speaker-labelled lines, or punctuation-delimited sentences.

    Sentence boundaries are whitespace after .!?; abbreviations are not inferred.
    Trimming span edges and removing utterance labels changes offsets, never source text.
    """
    if method not in ('paragraph', 'utterance', 'sentence'):
        raise ValueError(f'unsupported segmentation method: {method}')
    pattern = {'paragraph': r'(?:\r?\n)[ \t]*(?:\r?\n)',
               'utterance': r'\r\n|\n|\r',
               'sentence': r'(?<=[.!?])\s+'}[method]
    result = []
    start = 0
    for boundary in [*re.finditer(pattern, text), None]:
        end = boundary.start() if boundary else len(text)
        next_start = boundary.end() if boundary else len(text)
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        label = speaker
        if method == 'utterance' and speaker is None:
            match = re.match(r'([^:\r\n]{1,80}):[ \t]*', text[start:end])
            if match:
                label = match[1].strip()
                start += match.end()
        if end > start:
            result.append({'start': start, 'end': end, 'ordinal': len(result), 'speaker': label})
        start = next_start
    return result
