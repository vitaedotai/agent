# Vitae for agents

Public home for connecting AI assistants to [Vitae.ai](https://vitae.ai).

This repository is an initial scaffold. Client packages and installation instructions will be added and verified before release.

## Scope

- Connection guides and manifests for Claude, Codex, Cursor, Grok, and other supported clients.
- A core Vitae operating skill covering workspace context, available tools, approvals, and outcomes.
- Troubleshooting and client compatibility documentation.

Vitae's hosted MCP endpoint is `https://mcp.vitae.ai/mcp`. See the [setup page](https://mcp.vitae.ai) for current connection guidance.

Recruiting workflows belong in [vitaedotai/skills](https://github.com/vitaedotai/skills). The hosted service implementation remains in the private product repository.

## Layout

- `skills/`: the core Vitae operating playbook.
- `docs/`: client setup, compatibility, and troubleshooting guides.

Never commit credentials, customer records, or private product source.
