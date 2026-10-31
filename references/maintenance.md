# Maintenance and publication

Keep one canonical checkout of this package. Private workspaces and host entry
points refer to it; fixes to shared behaviour are made here. Host-specific files
should contain only a pointer and workspace location. The package works by
following Markdown links even without automatic skill discovery.

Package files must be generic. Blank templates contain no answers, favourite
works, exclusions, default audiobook ratio, country, or other personal taste.
Taste-related tests use fictional records. Parser fixtures can contain public
award/feed metadata, with no user's consumption or opinions attached.

## Public boundary

`PUBLIC_FILES.txt` is an exact publication allowlist. `.gitignore` ignores
everything else by default. Add new generic files deliberately to both after
reviewing their contents; do not generate a new allowlist from an unreviewed tree.
Never add personal data even temporarily: deleting it later leaves Git history.

Before a release run `python3 scripts/check_public.py` and the test suite. The
checker verifies working-tree and tracked paths, rejects symlinks and common
private paths/content, and checks committed paths for allowlist violations.
It is a backstop, not proof that prose contains no private preferences. Review
the actual staged diff and new files for personal details. Do not paste private
record snippets into release notes, commit messages or public issues.

Start this repository with fresh history, without the parent project's Git
directory or commits. Author identity is separate from taste records; never
include personal shelf data or answers in commit metadata. Only publish to a
repository destination explicitly chosen by its owner; host login/defaults do
not establish that choice.

Updates change shared code/instructions, leaving private data untouched. Preserve
record compatibility or provide a reviewed migration with a backup. Re-run the
blank-workspace and legacy-profile checks after changes. Host compatibility is
unverified until exercised in that host; document capabilities instead of claiming
that a tool-specific integration works everywhere.
