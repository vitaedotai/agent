# Install Vitae for an assistant

1. Identify the client and use the corresponding [README installation path](README.md).
2. For skill-only setup, select any bundled skill with `bunx skills add vitaedotai/agent --skill <name>` (for example `vitae` or `candidate-outreach`). This does not configure tools.
3. For tool access, register `https://mcp.vitae.ai/mcp` as a remote Streamable HTTP MCP server named `vitae`.
4. Use the client's OAuth flow. Leave browser consent and account selection to the user. Never request credentials in chat.
5. Confirm the intended workspace. Use the live catalog to verify authenticated status and job-list reads (`agent_status` and `list_jobs` when listed). Stop on auth or permission failures; do not change accounts automatically.
6. Report what was installed, whether authentication succeeded, and any remaining user step. No writes are needed for setup.
