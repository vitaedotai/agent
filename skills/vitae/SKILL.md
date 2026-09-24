---
name: vitae
description: "Operate Vitae through its hosted MCP connector: find ATS candidates and jobs, inspect pipelines, prepare drafts, and handle pending approvals. Use for work in a Vitae workspace, not generic recruiting copywriting."
license: MIT
metadata:
  version: "0.1.0"
---

# Vitae

Connect to `https://mcp.vitae.ai/mcp` using Streamable HTTP and the client's OAuth flow. Setup guidance is at https://mcp.vitae.ai. Never ask for passwords, cookies, tokens, or verification codes in chat. On an authentication failure, use the client's sign-in flow. Do not search local files for credentials or change accounts to bypass a permission failure.

## Establish context

1. Inspect the connected server's tool list. The [public tool snapshot](references/tools.md) is a dated reference, not a guarantee of the caller's permissions or the deployed tool set. Use the live input schema for every call.
2. Confirm the intended Vitae workspace from the user's request and authenticated context. If the connector cannot expose the workspace identity, ask the user to verify it in Vitae before reading sensitive records or writing. `agent_status` reports the agent provider, not the workspace identity.
3. Call `agent_status` and `list_jobs` as a read-only connection check. Public tool discovery alone does not prove authenticated access. Do not create a record or run a workflow to test setup.

## Find the right records

- Existing ATS candidate: call `search_ats_candidates` with the supplied name or query, resolve ambiguity, then pass the returned ID to `get_candidate` or `get_candidate_resume`. Never construct IDs from names.
- Job: call `list_jobs` with optional `search` or `clientId`, then `get_job` using the selected `jobId`.
- Client: call `list_clients`, resolve the client, then `get_client`.
- Pipeline: use `pipeline_summary`, `get_pipeline_board`, `list_applicants`, or `list_candidates_in_pipeline` according to their live schemas. A candidate ID and an application ID are different identifiers.
- `get_best_matches` reports persisted match scores, not a hiring decision or proof of a qualification. Present evidence and uncertainties separately.
- External sourcing is distinct from ATS lookup. The 2026-09-24 public catalog does not expose `start_sourcing_search` or `search_sourcing_pool`, even though some tool descriptions mention them. Do not call absent tools. Prepare the sourcing brief and hand it to Vitae's Sourcing surface, or use a later live tool only if it is actually listed and the user authorizes any paid search.

## Draft and change records

Read relevant records first. Show the proposed fields and target record when a mutation needs a user decision. Reuse explicit authorization already given for the same action and scope; do not add a blanket extra confirmation for harmless reads or drafting.

`create_job_draft` requires job details including description, company information, category, employment type, workplace type, location, and country. Ask for missing required facts rather than invent them to satisfy the schema. Creating a draft does not publish a vacancy.

Vitae routes business-record mutations through its approval system. Treat a returned pending approval as pending. Report its identifier and proposed change. Call `resolve_approval` only after the user explicitly approves or declines that specific action and only if permitted by the connected account. An earlier request to prepare a draft is not authorization to approve a later action with changed scope. Never infer completion from an approval request.

After a successful mutation, read back the resulting record when a read tool exists. On timeouts, inspect state before retrying non-idempotent creation or workflow calls. Do not create duplicate records or rerun a workflow just because a response was lost.

## Outreach and interviews

The public catalog currently has no direct email-send, calendar-booking, or candidate-presentation publishing tool. Draft those deliverables and hand them back to the recruiter in Vitae. `import_campaign_contacts` adds contacts to an existing campaign; it does not send an invitation and may expose contacts to the campaign's configured automation. Use it only for an explicitly requested import into a verified campaign.

Never use `run_workflow` or `ask_vitae` as a workaround for an unavailable send or booking capability. A workflow execution can cause external effects: inspect its intended behavior and obtain the required authorization. A successful queue response proves it was queued, not that emails were delivered.

For writing and recruiting methods, use separately installed skills from https://github.com/vitaedotai/skills. Those skills can work from supplied context without Vitae. Keep candidate information in the authorized task and workspace; do not place it in public examples, repositories, or telemetry.

## Report the outcome

Return the selected records, completed reads or writes, any pending approval, unresolved facts, and the next action. Use precise states: drafted, awaiting approval, queued, completed, or failed. Include only the personal information needed for the user's recruiting task.
