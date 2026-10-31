# Gathering commands and evidence

Run commands with the actual package path and an explicit private cache path.
`--help` is authoritative for individual options.

| Script under `scripts/` | Required source selection | Offline fixture input |
| --- | --- | --- |
| `refresh_hugo.py` | `--year YEAR`, optional official `--url URL` | `--html-file FILE` |
| `refresh_nebula.py` | `--year YEAR`, optional `--url URL` | `--html-file FILE` |
| `refresh_clarke.py` | `--year YEAR`, optional `--url URL` | `--html-file FILE` |
| `refresh_bsfa.py` | `--year YEAR`, optional `--url URL` | `--html-file FILE` |
| `refresh_locus.py` | `--year YEAR --url URL` | `--html-file FILE` |
| `refresh_locus_rrl.py` | `--year YEAR --url URL` (reading year, not announcement year) | `--html-file FILE` |
| `refresh_clarkesworld.py` | Optional `--url URL` | `--rss-file FILE` |
| `refresh_escape_pod.py` | Optional `--url URL` | `--rss-file FILE` |

Every refresh accepts `--cache-dir /absolute/private/workspace/findings`.
For example:

```sh
python3 /path/to/package/scripts/refresh_hugo.py --year 2024 \
  --cache-dir /path/to/private/workspace/findings
```

Years here illustrate syntax, not a current-source recommendation. Source pages
and layouts change: verify the fetched page matches the intended list and inspect
parsed members. RSS and HTML fixtures bundled with tests are parser examples,
not fresh research. Refresh functions preserve older findings as soft-stale
archives; source pages are not bulk-harvested.

The Finding store uses `finding_id`, `kind`, `payload`, `source_refs`, `fetched_at`,
`max_age_seconds`, and `status`, with optional `validated_at` and `swr_seconds`.
Use `finding_cache.store.write_finding` and `to_gate_finding` rather than a
parallel schema. Living List payloads contain `members` with title, creator,
category and year. Store Discoverable Facts separately where appropriate.

Refresh only metadata needed for the question; avoid story bodies and spoiler
descriptions. For novel/novella discovery, `recommend_pull.py --medium books`
excludes novelettes; `short` is separate. `screen` currently uses Dramatic
Presentation categories. The existing long/short form labels are category-based
hints: verify actual film/episode/series form before delivery. Manual researched
lanes remain available when no parser covers the medium.
