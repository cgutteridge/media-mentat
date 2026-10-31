# Private workspaces

The package installation is reusable code and instructions. A private workspace
is a user-selected directory outside that installation, containing:

```text
taste/grilling-record.md   # Answers, clusters, constraints, consumption
taste/inventory.md         # Shelf observations and identification confidence
sources.md                # Private additions to public source defaults
findings/                 # User's Finding cache, including archives
research/                 # Candidate evidence and fact checks
history/                  # Recommendations and feedback
```

Existing layouts may be used without migration. Preserve established record
sections, certainty rows and source registries. Establish the paths explicitly;
never search unrelated user directories for profiles. Do not create a second
record for an established user. Legacy formats can retain richer personal files.

The CLI accepts explicit `--cache-dir` and `--grilling-record` paths. Compatibility
defaults resolve from the calling working directory, not the package location.
Personal writes inside the package, including paths that resolve there through
symlinks, are rejected by the provided workspace initializer and Finding store.
Agents must apply the same rule to their direct file writes.

For a new user, run:

```sh
python3 /path/to/package/scripts/init_workspace.py --workspace /absolute/private/workspace
```

This creates only missing files; rerunning preserves answers and local sources.
The blank template starts with no taste facts, consumption rows or exclusions.

Keep `## Consumption certainty` as a Markdown table with columns `Title`,
`Creator`, `Certainty`. The parser uses `Title — Creator` as its work identifier.
Use canonical spellings consistently; check aliases before adding a duplicate.
Unlisted works are `unknown`. `won't-read` requires an explicit decision to skip
the work **and acceptance of spoilers**. DNF, dislike and “not now” are separate
feedback, not spoiler permission.

Each taste cluster records anchors, user-stated reasons, context, exceptions and
separately labelled hypotheses. Session addenda retain dated answers; the summary
is a maintained interpretation of that evidence. Corrections should explicitly
supersede the old statement rather than silently erase its provenance.

Read `references/sources.md` as the shared defaults and workspace `sources.md` as
an overlay. Local retirements or corrections override defaults for that workspace;
do not auto-copy default registry changes over personal notes.
