---
name: research
description: Gather evidence for personal media advice using official lists, bibliographies, criticism and edition checks. Use for suitability assessments, possible turn-offs, discovery, or missing and stale evidence.
---

# Research pass

Read the [main skill](../../SKILL.md), the relevant private taste clusters and
constraints, [source defaults](../../references/sources.md) and the private
`sources.md` overlay. Determine which lane, medium, date range or factual question
needs evidence. The defaults describe SF/fantasy coverage, not the user's taste.
For a supplied work, research that work directly; award/list membership is not a
prerequisite for advice. Extend to nonfiction or other media with appropriate
sources and explicit coverage limits. Verify requested concerns separately from
positive fit evidence; no mention of a concern is not evidence of its absence.
When registry coverage is inadequate for the genre, medium or kind of claim,
follow [Add source](../add-source/SKILL.md). Read
[media.md](../../references/media.md) when a new medium requires different fit
criteria, such as game mechanics or documentary treatment.

## Living Lists

Read [gathering.md](../../references/gathering.md) for supported refreshers and
commands. Prefer official awards lists and published feeds. Refresh only needed
lanes and years into the **private** `findings/` directory using explicit absolute
`--cache-dir` arguments. Inspect the parsed output for correct year, category,
work identity and reasonable coverage. A successful request with zero parsed
members is not adequate evidence. Preserve source URL and fetched time; failed
parsing does not count as refreshed evidence. Do not relabel cached data as newly
fetched without actually checking the source.

Re-run the pull CLI/Evidence gate after refresh. Findings beyond soft reuse
remain blocked until refreshed. Stable Work identity itself has no freshness
expiry; Living List membership and Discoverable Facts do.

## Bibliographies, adjacency and candidate facts

For gaps, check an official bibliography or reliable bibliographic source for a
creator the user has actually touched. Research a narrow next-work question;
avoid treating “gap” as permission to invent an unrelated shortlist.

For adjacency, start from a confirmed cluster's **reason for enjoyment**. Indexes
and trope pages can suggest cousins, but have high spoiler risk and are not
Living List authority. Community discussions are leads requiring verification,
not unread-safe list-refresh sources.

Verify candidate fit with publisher/creator material or appropriate independent
criticism, recording source URLs, accessed dates and only needed mood/theme/craft
evidence. Use regional edition/provider pages for availability, narrator, runtime
and commitment; ask region if necessary. Time-sensitive claims need current
evidence. Avoid unnecessary synopsis, excerpts and review spoilers.

Save user-targeted research in private `research/` notes (or Discoverable Fact
cache records using the store schema). Record which question each source supports.
An award listing supports membership, not every claim about style or suitability.

## Source upkeep

Append useful sources to the private overlay with role, medium, spoiler risk,
URL and verification date. Retire dead sources with a reason. General source
defaults may be improved during package maintenance after removing all user
associations; recommendation sessions write to the private overlay.
Source selection/validation and registration live in the add-source subskill;
this workflow gathers candidate evidence from the selected sources.

Finish with evidence for the requested question, a gate result where applicable,
and explicit unsupported areas. If required tools or sources are unavailable,
state that limitation and pause that lane. Never substitute model recollection
for a Research pass.
