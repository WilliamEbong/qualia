# Native subscription classification

The owner approved practical native generation and invocation-accounting limits in docs/answers/01-native-usage.md. Enable existing classification adapters without enabling file-editing operators or modifying account settings.

## Requirements

- FR001: Public Claude/Codex classification is available when its official executable is installed; dispatch must reject unaudited versions before any model call.
- FR002: Preserve empty cwd, no action tools, allowlisted environment, strict schema/record validation, 90-second default deadline and bounded input/output. Codex's local limits must never be described as a provider token cap.
- FR003: Reserve one invocation before every native dispatch; retain failed reservations and reported aggregate usage. Disable automatic router retries for native providers, keep native batches at most five segments, and preserve other providers' behavior.
- FR004: Document that native call/egress counts represent CLI invocations and may include several provider requests. Preserve exact per-request Jev accounting and offline behavior.
- FR005: Each user's official local subscription sign-in is used; no API-key fallback, copied credentials, account mutations or elevated setup. Operators remain unavailable.
- FR006: Verify public dispatch, missing/unsupported CLI, egress/budget denial, internal continuations and bounded failures offline, then run one synthetic live invocation per approved native classifier through the normal router when possible. External failures remain explicitly reported.

## User scenarios

A researcher installs/signs in to the official CLI, deliberately enables external processing for a project, and runs a small classification batch from Qualia. Results become suggestions for review. Missing login, quota exhaustion, version mismatch or provider failure returns a sanitized error and keeps usage admission recorded. The file-editing improvement operator remains disabled.

## Success criteria

- SC001: Targeted native/router/ledger tests pass, including no-dispatch denials and one reservation per launched invocation.
- SC002: Actual live result or precise external limitation is recorded per provider; no fake live claim.
- SC003: Review UI and installation guide explain local account ownership and invocation-count semantics; Playwright verifies changed UI copy.
- SC004: Protected source/guard/runner files and methodology remain unchanged; no billing or account settings modified.
