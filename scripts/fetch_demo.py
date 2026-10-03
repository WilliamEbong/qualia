"""Fetch exactly the licensed, pinned AnnoMI CSV without changing existing bytes."""

import hashlib
import urllib.request
from pathlib import Path

from qualia.io.demo import SOURCE_SHA256, SOURCE_URL


def fetch_demo(target=None):
    target = Path(target) if target is not None else Path(__file__).resolve().parents[1]/'demo/data/AnnoMI-simple.csv'
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != SOURCE_SHA256:
            raise ValueError('existing AnnoMI file checksum mismatch; file preserved')
        return target
    # urllib's standard HTTPS opener verifies certificates; no custom unverified TLS context.
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        if not response.geturl().startswith('https://'):
            raise ValueError('AnnoMI fetch redirected outside verified HTTPS')
        raw = response.read(4_000_001)
    if len(raw) > 4_000_000 or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('downloaded AnnoMI checksum mismatch; nothing published')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    return target


if __name__ == '__main__':
    print(fetch_demo())
