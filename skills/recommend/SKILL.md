---
name: recommend
description: Deliver evidence-gated fiction shortlists and creator gap fills from a private taste record and researched sources. Use for narrative-media recommendations and continued discovery.
---

# Evidence-gated recommend

Apply the [main skill](../../SKILL.md). Read [workspace.md](../../references/workspace.md)
for paths and record format. Work in the established private workspace.

## Load and scope

Load the private record's Consumption certainty, Constraints, Taste clusters and
Session addenda, plus the public source defaults and private source overlay.
For legacy records also load Text-session addenda constraints/checklists and
binge/dislike notes. Read voice transcripts only when a specific ambiguous answer
blocks a decision. Search relevant title/creator aliases once candidates exist.

Missing taste evidence routes to setup or a focused interview question. Learn
medium, format and comfort/stretch needs from the record or request; avoid
inheriting package author's preferences. Mixed media are welcome when supported.
The current pull CLI supports books (novel/novella), screen and short fiction;
unsupported media require a Research pass with explicit evidence rather than a
fabricated CLI result. Comics/games can use verified bibliography gap research.

## Pull and gate

Use the packaged CLI, substituting the actual installation and workspace paths:

```sh
python3 /path/to/package/scripts/recommend_pull.py \
  --cache-dir /path/to/private/workspace/findings \
  --grilling-record /path/to/private/workspace/taste/grilling-record.md \
  --medium books
```

Use `screen` or `short` for those requests; run each relevant medium separately.
`--require ID` can name required findings. An empty cache blocks Living List
delivery. Do not hand-roll a parallel gate path.

- `allow`: continue; mention advised refresh if `refresh_suggested`.
- `must-refresh`: use [research](../research/SKILL.md) on blocked findings before pitching.
- `clarify-or-refuse`: resolve missing evidence or explain the affected lane's limitation.

## Filter and check prior experience

Apply every relevant recorded exclusion and contextual constraint. Check title,
creator and aliases against certainty, inventory answers, binge/auto-buy notes,
prior recommendations and rejections. A creator-level binge note is a reason to
ask or drop a candidate, never a synthetic per-work consumption confirmation.
Do not present consumed, declined or previously rejected works as fresh finds.
Ask one focused clarification when it would materially change the shortlist.

Log rejected candidates and reasons privately in dated history or Session
addenda (including an empty rejection list). An inventory observation alone does
not establish consumption, dislike or preference.

## Deliver and remember

Unless narrowed by the user, offer comfort and stretch tied to **their** clusters.
Stretch can deepen a different kind of enjoyment; it need not interpolate between
two favourites. Adjust size and balance to evidence and the request. Add narrowly
researched creator gaps where useful.

Each pick includes title, creator, medium, lane (`fun`, `stretch` or `gap`), an
Unread-safe reason tied to a stated preference, and a verified format/commitment
note. Identify speculative fit as such. Evidence is required:

- Living List picks: `finding_id: ID`, with relevant gate allow and actual membership.
- Bibliography gaps: `gap: rationale`, with a source link and private research note.
- Other researched candidates: `research: private-note-id`, with supporting public
  source links. Adjacency leads never borrow a Living List finding's authority.

Separate source-supported facts from the fit inference. Omit unverified regional
availability claims. Keep every unconfirmed work Unread-safe regardless of how
familiar its title seems.

Save the offered titles and feedback in the private history. Persist explicit
answers in dated Session addenda, and update certainty rows only when confirmed.
Recommend sessions never write user data to the public package or to an external
notebook. Offer a targeted interview only when feedback reveals a real gap.
