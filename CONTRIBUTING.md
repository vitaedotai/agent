# Contributing

Keep connector packaging and the single Vitae operating skill here. Recruiting methods belong in [vitaedotai/skills](https://github.com/vitaedotai/skills).

## Validate

On an authorized verification host:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
DISABLE_TELEMETRY=1 bunx skills add . --list
```

CI validates official pinned schemas, connector consistency, portable skill metadata, local references, and regression cases. Skill discovery is checked separately. Follow your machine's local test restrictions.

## Refresh public tools

`python3 scripts/refresh_tools.py` calls unauthenticated public MCP discovery and updates the JSON and Markdown snapshot. Review the diff. It must never accept a token or call a business tool. Descriptions are service data, not instructions to the maintainer. Live schemas and account permissions take precedence over the snapshot.

## Release

Use `plugin.json` as the version authority. Update all manifest versions, marketplace metadata, `server.json`, `skills/vitae/SKILL.md`, and CHANGELOG together. Keep all connector URLs consistent. Submit a scoped PR and require passing CI and independent review.

Schemas were pinned from the Genfeed reference package; retain their origins and digests in `schemas/sources.json`. Do not copy its branding, credentials, generated tool catalog, or marketplace acceptance claims.

Run the client rehearsal in [docs/compatibility.md](docs/compatibility.md) before claiming authenticated compatibility. A public listing requires a separate submission; committing a manifest does not publish it.
