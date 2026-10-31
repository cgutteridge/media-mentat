---
name: fiction-recommender
description: Learn a user's narrative-media tastes from shelf photos and conversation, research candidates, and recommend fiction with spoiler and evidence checks. Use for initial setup, taste interviews, recommendation feedback, and fiction discovery.
---

# Fiction recommender

Use this package with any agent that can read files and hold a conversation.
Use the host's available image, web and command tools; no particular app,
connector, background agent or separately installed skill is required.

## Workspace and privacy

Establish an explicit **private workspace** outside this package before writing
user data. Resolve relative workspace paths against the user's working directory,
never against the skill installation. Existing records stay authoritative; reuse
them without restarting setup. Read [workspace.md](references/workspace.md) when
creating, locating or changing a workspace.

Keep photos, inventories, answers, taste clusters, consumption, exclusions,
recommendation history and research selected for a user in that workspace.
This package contains reusable instructions, generic source defaults, blank
templates, code and synthetic tests only. Never copy a private record into an
example, test fixture, issue, commit message or public documentation. General
improvements belong here only after removing personal details and preference
defaults. Read [maintenance.md](references/maintenance.md) when editing or releasing
the package.

## Route

Read only the subskill needed for the current request. Relative links are ordinary
files: follow them directly if the host has no nested-skill discovery.

| Situation | Instructions |
| --- | --- |
| New user or missing taste record | [Setup](skills/setup/SKILL.md) |
| Initial questions, changed tastes, uncertain fit, repeated misses | [Interview](skills/interview/SKILL.md) |
| Missing/stale evidence, source discovery, bibliography or availability checks | [Research](skills/research/SKILL.md) |
| Shortlist, recommendations or gap fills | [Recommend](skills/recommend/SKILL.md) |

SF/fantasy is the initial source coverage, not an inferred personal preference.
Learn formats, exclusions, length, region and comfort/stretch balance from the user.
Support multiple distinct taste clusters; liking two works does not imply liking
their midpoint or every shared genre/trope.

## Shared rules

Use [the glossary](references/glossary.md). Delivery is **Unread-safe**: mood,
theme and craft without plot revelations, unless the per-work Consumption certainty
is `consumed` or explicitly `won't-read`. Unlisted works are `unknown`.
Declining a work, abandoning it or owning it does not grant spoiler permission.

Recommendations need the private taste record, source evidence and any required
Finding cache records. Missing evidence or findings stale beyond soft reuse block
the affected lane: research, ask a focused question, or explain the limitation.
Model recollection alone is not research evidence.

When image inspection is unavailable, request a typed shelf list. When web access
is unavailable, use valid local evidence or pause the unsupported lane. When file
writes are unavailable, offer a record for the user to save and explain that it has
not been persisted. Do not claim tool execution, memory or host compatibility that
has not been verified.
