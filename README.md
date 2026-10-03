# Qualia

Qualitative coding you can audit.

A local-first research workspace for reading transcripts, coding by hand, reviewing AI suggestions and measuring improvements against a protected benchmark. Human researchers control methodology; every coding decision keeps its provenance.

**Build in progress.** See [build state](docs/BUILD-STATE.md) for verified functionality. This repository is private until its owner elects to publish it.

## Development

Python 3.14, Node 24 and Git are required. Use `uv sync` to install Python dependencies. Research projects belong outside this checkout, under `%USERPROFILE%/Qualia` by default. Never commit research data or credentials.

## Decisions

- CLI subscription providers use the user's own installed, authenticated CLI. No login tokens are read or proxied.
- The existing ratified constitution and source runbooks are preserved.
- Configuration files use JSON syntax, which is valid YAML 1.2, to avoid a new YAML dependency.
- Jev is optional and off by default. [Setup instructions](docs/JEV-SETUP.md) cover the owner-managed key and billing steps.
- The app repo is code-only; workspaces have separate storage and Git histories.

MIT license. Dataset licenses will be recorded independently in DATA-LICENSES.md before demo publication.
