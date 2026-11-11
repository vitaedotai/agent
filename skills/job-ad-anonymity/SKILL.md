---
name: job-ad-anonymity
description: "Check a job advert before it is published or sent to job boards for client names, people, contact details and internal notes, then suggest anonymised wording."
license: MIT
metadata:
  version: "0.3.0"
---

# Job ad anonymity

## Inputs

Start with the exact text that will be public: title, description, about-the-company text, location, screening questions, apply email, and any link slug or tag that travels with the ad. Also collect what must not appear: the client name and its variants, client contacts, and any internal notes. In Vitae these come from the job and its linked client. Otherwise ask the recruiter for them.

First settle the mode. An agency advert for a client is anonymous by default. If the recruiter says the client has agreed to be named, or the advert is the employer's own, naming the company is allowed; still check every other category below. Record which mode was used and who said so.

## Procedure

1. **Confirm the source fields.** Recruiting systems keep an internal job title and description (written for the recruiter and often naming the client) apart from a public advert title and description. The public text is the only valid source. If the supplied text could be the internal version, or an import copied the internal fields, say so and stop: do not repair internal text by deleting a few words. Ask for the advert fields.
2. **Build the identifier list.** From the client record and the job, list: legal and trading names, abbreviations, former names, brands and products, website and email domains, office addresses and small localities that point to one site, client contacts' names, and the hiring manager's name or first name. Add any name or contact detail the recruiter supplies.
3. **Scan every public field,** not only the description. Check for the listed identifiers, but also read for what a list cannot catch:
   - **Block:** the client's name or abbreviation; its website, social profile or email domain; names, email addresses and phone numbers of client staff; personal email addresses (for example a webmail address); candidate names.
   - **Fix:** a hiring manager's name in any phrasing ("James is looking for", "reporting to Sam"); internal notes ("per client call", "replacement for Priya", "exclusive", fees, margins, rate negotiation room); a named product, project, or customer that points to one company; a street address or building.
   - **Review:** combinations that identify one employer even without a name, such as a rare sector, a specific town, a headcount and a founding year together; a job title that exists at only one company; text that matches a client's own public careers page.
   - **Fine:** the agency's own name and the agency consultant's work contact details, when that is how applications are meant to arrive.
4. **Rewrite, do not delete.** For each finding give the excerpt, the field, the reason, and replacement wording that keeps the useful fact in generic form (for example, "a regional property management firm" for a named firm). Do not invent facts to fill the gap: no made-up size, sector or location. If the generic form needs a fact you do not have, ask the recruiter. Do not swap a name for an initial, a partial name, or an obvious hint.
5. **Check the result against the list again.** Re-scan the rewritten advert for the same identifiers and for new ones introduced by the rewrite.
6. **State the limits.** A passing check is not a guarantee: a reader can still infer an employer from context, and an advert already live may be cached or copied by job boards. If the advert has already been published or sent, say that the live copies must be replaced on each board and re-checked there; fixing the source record does not change them.

## Output

Return a verdict: clear to publish, fix before publishing, or cannot assess (with the missing input). Then a findings table (field, excerpt, category, why, suggested wording), the full rewritten advert, the source fields used, the mode and who confirmed it, and anything not checked (attachments, linked pages, fields you could not see). Keep the findings report internal: it names the client and the contacts it protects, so do not send it to a job board or a candidate.

## Quality check

Does every Block finding have replacement wording or a clear next step? Was the check run on the public advert fields, not the internal ones? Does the rewrite still describe the same job, with no new invented facts? Are the identifiers that were found also removed from the apply email, location and tags?

## Example

Fictional internal text: "Sales Negotiator for Harbour Lane Estates. Sam Okafor (sam@harbourlane-estates.example) wants someone by June; client is paying 22% fee, replacing Priya." Finding: client name, a client contact's name and email, the fee and a former employee's name. Suggested public text: "Sales Negotiator for an independent estate agency in the harbour district. Start date by June." Ask the recruiter whether "harbour district" is acceptable, since a small town plus a sector can still point to one firm.

## With Vitae

If connected, use `get_job` for the advert fields and `get_client` or `list_clients` for the client name and contacts. Never guess IDs. Read the advert fields, not only a title returned by a list. Reads need no approval. Preparing the check and the rewrite is drafting. Only call `update_job` after the user has asked for the change, with the exact fields; treat an approval response as pending, not done, and read the job back afterwards. Do not publish a job or send it to a job board unless the user asked for that action and a verified tool exists. If no tool can do it, hand the recruiter the clean text and the exact fields to replace in Vitae.

## Completion and handoff

The task ends with a verdict and, where requested, a verified read-back of the updated fields. After a fix, hand the clean text to the recruiter for publishing. Pair it with `job-intake` when the brief itself mixes confidential client notes with public requirements, and with `candidate-presentation` for the same check on candidate documents.
