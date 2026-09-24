<p align="center"><a href="https://vitae.ai"><img src="assets/logo.png" width="96" height="96" alt="Vitae.ai" /></a></p>

# Vitae for AI assistants

Find candidates, inspect jobs and pipelines, and prepare recruiting work from your assistant.

This package combines **one Vitae operating skill** with the hosted connector. The broader recruiting catalog lives in [vitaedotai/skills](https://github.com/vitaedotai/skills).

## Connect

```text
https://mcp.vitae.ai/mcp
```

Use Streamable HTTP and complete Vitae OAuth in your client. A Vitae account and access to the intended workspace are required. Public discovery works without signing in; accessing recruiting records does not.

## Install

### Claude Code

```text
/plugin marketplace add vitaedotai/agent
/plugin install vitae@vitae
```

Open `/mcp`, select Vitae, and finish OAuth. MCP-only alternative:

```bash
claude mcp add --transport http vitae --scope user https://mcp.vitae.ai/mcp
```

### Codex

```bash
codex plugin marketplace add vitaedotai/agent
```

In a supported Codex client, refresh the plugin sources and install Vitae. Registering the source alone does not install the package. MCP-only alternative:

```bash
codex mcp add vitae --url https://mcp.vitae.ai/mcp
codex mcp login vitae
```

### Cursor

Add the remote server in Cursor's MCP settings:

```json
{"mcpServers":{"vitae":{"url":"https://mcp.vitae.ai/mcp"}}}
```

This connects tools only. Install the operating skill with the Skills CLI below. This repository also includes a native Cursor plugin manifest; it does not imply a public Cursor marketplace listing.

### Grok

For Grok chat, add a custom connector with the MCP URL and authenticate. Grok Build packaging is in `.grok-plugin/`, with the same operating skill and hosted connector. Chat connectors and Build plugins are separate installation surfaces. No public Grok marketplace listing is claimed.

### Gemini CLI

```bash
gemini extensions install https://github.com/vitaedotai/agent
```

Complete OAuth when prompted. The extension loads `GEMINI.md` and the operating skill.

### Skill only

```bash
bunx skills add vitaedotai/agent --skill vitae
```

This installs instructions only. Configure the connector and sign in separately.

## Try it

- “Show my open jobs in Vitae.”
- “Find this candidate in my existing ATS and summarize the evidence relevant to this job.”
- “Prepare a candidate presentation for this role, including missing information.”

The current public catalog does not expose direct email sending or calendar booking. Skills can draft messages and interview plans; the recruiter completes those actions in Vitae unless a verified, authorized tool supports them. Business-data changes can return a pending approval instead of executing.

## Verification and privacy

Setup succeeds when authenticated `agent_status` and `list_jobs` calls succeed in the intended workspace. Tool listing alone is insufficient. See [compatibility and acceptance](docs/compatibility.md), [data handling](docs/privacy.md), and [the operating skill](skills/vitae/SKILL.md).

No local daemon, hooks, or telemetry are installed by this package. Tool arguments go to Vitae's hosted MCP service and its API. Your AI client also handles the conversation according to its own settings.

[Vitae.ai](https://vitae.ai) · [MCP setup](https://mcp.vitae.ai) · [Documentation](https://docs.vitae.ai/reference/mcp) · [Contributing](CONTRIBUTING.md)

[LinkedIn](https://www.linkedin.com/company/vitae-ai) · [X](https://x.com/vitaeai) · [Open Vitae](https://app.vitae.ai)
