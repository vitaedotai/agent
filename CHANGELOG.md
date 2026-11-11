# Changelog

## 0.3.0

Added the `job-ad-anonymity` skill: before a job advert is published or sent to job boards, check the public advert fields for client names, client staff, contact details and internal notes, and suggest anonymised wording. It requires the public advert title and description rather than internal job fields, and states that adverts already live must be replaced on each board. Updated the bundle from ten to eleven skills, the catalog, the Grok skill list, the routing table, and the validation checks.

## 0.2.4

The OpenAI manifest now carries the review test cases (five positive, three negative) so the upload ZIP supplies them to the portal. Reviewer credentials stay in the portal and are never stored in this repository. `tools_triggered` is a comma-separated string, as the portal requires.

## 0.2.3

The OpenAI upload ZIP now declares OAuth for the hosted connector (`extensions["com.openai"].auth`, client metadata document mode) so the portal can authenticate instead of reporting authentication unavailable. The portable `mcp.json` is unchanged.

## 0.2.2

Clarified how to list the ten bundled assistant skills. Candidate/job competencies returned by `search_skills` and internal engineering skills are separate catalogs, and must not be presented as Vitae plugin workflows.

## 0.2.1

Added the OpenAI support URL, selected Business & Operations for recruiting workflows, clarified the listed capabilities, and designated the bundled Vitae operating skill for onboarding.

## 0.2.0

Unified the hosted connector, app operating skill and nine recruiting workflows in one Vitae plugin. This repository now owns all ten skills. Added catalog completeness checks, individual-install reference checks, and a reproducible portable OpenAI ZIP. Updated live-capability guidance for invitations and removed the need to install a second recruiting plugin. Directory publication and connected client acceptance remain separate.

## 0.1.0

First installable release. See README for available capabilities and validation boundaries.
