# Maintaining the Vitae agent package

This public repository is the canonical source for the unified Vitae plugin: hosted connector, one platform operating skill, and nine recruiting workflows. Keep product implementation and customer information out of it. The old `vitaedotai/skills` repository is a historical snapshot, not a second active source.

- `plugin.json` is the release-version authority. Keep native manifests, marketplace metadata, `server.json`, catalog.json, every skill version, and CHANGELOG aligned.
- Use the actual live tool schema. Refresh the public snapshot with `python3 scripts/refresh_tools.py`. Never invent tools or publish authenticated responses.
- Keep every connector pointed at `https://mcp.vitae.ai/mcp`. OAuth is the default; never embed credentials.
- Run `python3 scripts/validate.py` and the regression suite on an authorized verification host. Follow the user's host restrictions.
- A green packaging check is not authenticated client acceptance. Record actual client results in `docs/compatibility.md`; never claim a marketplace listing merely because its manifest exists.
- Use scoped branches and PRs. Do not weaken Vitae's server approval controls through skill wording.

- Keep all ten skill folders under `skills/`, with local resources inside each folder so individual installation remains self-contained. Validate catalog parity and build the portable upload ZIP with `python3 scripts/package.py`.
- Required current-head CI governs merge. Separate reviewers require an explicit user request.
