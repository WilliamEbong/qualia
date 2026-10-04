# Jev fixture provenance

`tests/test_jev_backend.py` builds hand-authored synthetic HTTPX MockTransport responses
from the public OpenAPI contract, checked 2026-10-03. These cover all three primitive
shapes and adversarial replies. They are **not recorded live API responses**.

Those hand-authored wire examples use no real account key or research text and must
not be relabeled as captured provider evidence.

`live-normalized.json` is separate: a successful owner-authorized synthetic request
on2026-10-03 through the normal router and Jev adapter. It records the **normalized
adapter result**, not the raw HTTP body. The sentence and codebook are invented;
no headers, credentials, account identifiers or private research were captured.
Returned model:jev-1.13.0;425 input/23 output tokens;$0.00001785 recorded cost.
The offline regression verifies the normalized application contract and cost basis.
