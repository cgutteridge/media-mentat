# Fiction recommender skill

Portable Markdown workflows for learning narrative-media tastes and researching
recommendations. SF/fantasy source coverage is included; personal tastes start
blank. Python helpers require Python 3.11+, with no runtime third-party packages.

Clone the whole repository and ask your agent to read [SKILL.md](SKILL.md), giving
it an explicit private workspace path outside the checkout. The entry point links
setup, interview, research and recommendation subskills as ordinary files. A host
can expose that entry point through its own skill mechanism or a thin instruction
pointer. No app-specific integration or Google account is required. Markdown
workflows are portable; individual host integrations have not been certified.

New setup starts with photos of books or DVDs/Blu-rays, then confirms consumption
and asks why particular works appeal. A typed list works when image inspection
is unavailable. Distinct tastes remain distinct; the interview does not average
all preferences into one nexus.

Create a workspace, or let the setup workflow do so:

```sh
python3 scripts/init_workspace.py --workspace /absolute/private/workspace
```

All user data stays there. Agents need file access to persist records, image
inspection for shelf photos, web access for new research, and command execution
for the provided helpers. Without a capability, follow the documented fallback
and state the limitation. Existing profiles can be used without restarting setup.

Keep the checkout as the source of shared behaviour and update it independently
of private records. See [maintenance](references/maintenance.md) for the exact
public-file allowlist, privacy checks and release review.

Validate locally:

```sh
python3 scripts/check_public.py
python3 -m pytest
```

Parser fixtures contain public list metadata; taste/consumption tests use invented
records. Fixtures are not fresh research. The privacy checker cannot determine
whether arbitrary prose reveals someone's preferences: review every public diff.
