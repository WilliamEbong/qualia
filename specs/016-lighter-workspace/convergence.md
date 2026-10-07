# Lighter workspace convergence

Three requirements, two success criteria, three tasks: converged.

- FR001/FR003: `GET /api/projects/{slug}` returns `current_coding_ids` (8,021 IDs on the demo copy) and an empty `current_codings`; stored data, analysis and exports are unchanged.
- FR002: `hydrateWorkspace` rebuilds rows by ID; embedded demo rows are used as-is (unit test).
- SC001: 13.46 MB → 7,417,672 bytes (−45%). Playwright on the demo copy: 36 segments in the first transcript, current assignments shown, matrix counts and Analysis rendered with no error.

Not covered: Lighthouse was not re-run in this session; the remaining 7.4 MB is mostly `coding_events` (5.6 MB), which the provenance views and analysis evidence use.
