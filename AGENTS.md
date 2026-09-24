# Maintaining the Vitae agent package

This public repository packages the connector and one operating skill. Keep product implementation and customer information out of it. Recruiter methods belong in `vitaedotai/skills`.

- `plugin.json` is the release-version authority. Keep native manifests, marketplace metadata, `server.json`, the skill version, and CHANGELOG aligned.
- Use the actual live tool schema. Refresh the public snapshot with `python3 scripts/refresh_tools.py`. Never invent tools or publish authenticated responses.
- Keep every connector pointed at `https://mcp.vitae.ai/mcp`. OAuth is the default; never embed credentials.
- Run `python3 scripts/validate.py` and the regression suite on an authorized verification host. Follow the user's host restrictions.
- A green packaging check is not authenticated client acceptance. Record actual client results in `docs/compatibility.md`; never claim a marketplace listing merely because its manifest exists.
- Use scoped branches and PRs. Do not weaken Vitae's server approval controls through skill wording.
