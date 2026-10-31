# Media Mentat

A private media adviser with a carefully maintained understanding of your tastes
and a politely elevated opinion of its own judgment. Recommend things to read,
watch or play; assess suggestions from other people or its own earlier advice;
and add personal-fit feedback to a list. Answers can live in chat or documents.

The voice takes broad inspiration from Lynch's Mentats and Alfred's dry,
affectionate competence: attentive service, independent judgment, occasional wit.
Your preferences remain yours. See [the house voice](references/voice.md).

## Start

Clone the whole repository and ask your agent to read [SKILL.md](SKILL.md), giving
it an explicit private workspace path outside the checkout. The linked subskills
are ordinary Markdown files. A host can expose the entry point through its own
skill mechanism or a thin pointer; no particular app, connector or account is required.

Setup begins with photos of books, DVDs/Blu-rays or games, then an adaptive quiz:
what you like about particular works, and A-or-B comparisons that explore why.
Typed lists or digital-library screenshots can supplement or replace shelf photos.
Distinct kinds of enjoyment stay distinct rather than becoming one averaged taste.

Setup also checks source coverage. The shipped lists focus on SF/fantasy; they do
not limit the tool's interests. If your genres or media need other lists and reviews,
Media Mentat recommends targeted source research and uses the add-source workflow.
Gaming, documentaries, nonfiction and other areas can use appropriate researched
sources even without a dedicated automated parser.

## Requests

- “Recommend three things I could play in short sessions.”
- “Would I like Blade Runner?”
- “My friend recommended Blood Meridian. What might put me off?”
- “Add feedback to this list.”
- “Make a recommendation document with appeal, possible friction and sources.”
- “Find and add reliable review and discovery sources for this genre.”

Assessments distinguish appeal, possible turn-offs, confidence and missing evidence.
Warnings follow per-work spoiler rules; asking about a concern does not grant plot
spoilers. New genres/media use [adaptation guidance](references/media.md).

Document work preserves the original list and clearly attributes added feedback.
Markdown is the portable default for new files; other formats/editors use whatever
capabilities the host actually provides. Exact external destinations need user
authorization. No Google Doc extension is bundled.

## Private data and capabilities

Create a workspace, or let setup do so:

```sh
python3 scripts/init_workspace.py --workspace /absolute/private/workspace
```

Personal records, photos, findings, research and generated documents stay outside
the package. Blank templates contain no inherited tastes. Update the shared
checkout independently of those records. See [maintenance](references/maintenance.md)
for the exact public-file allowlist, privacy checks and release review.

Python helpers require Python 3.11+, with no runtime third-party packages. Agents
need file access to persist records, image inspection for photos, web access for
new source/candidate research, and command execution for helpers. Missing
capabilities have explicit fallbacks. Markdown workflows are portable; individual
host integrations and document formats have not been certified.

Validate locally:

```sh
python3 scripts/check_public.py
python3 -m pytest
```

Parser fixtures contain public-list or synthetic metadata; taste/consumption tests
use invented records. Fixtures are not fresh research. Privacy checks are a
backstop, not proof that arbitrary prose contains no private preferences: review
every public diff.
