# Recommendation vocabulary

**Stable Work**: An identified media work, fiction or nonfiction. Identity is stable; editions and
adaptations may need distinct identifiers. A work itself does not become stale.

**Living List**: A collection whose membership can change, such as an award
shortlist or magazine feed. Its cached evidence has a freshness policy.

**Discoverable Fact**: Evidence about a work that may become newly discoverable or
change, such as an award, adaptation credit or regional availability.

**Finding cache**: Persisted research records with source references, timestamps
and freshness rules. Reusable across sessions in a private workspace.

**Research pass**: Deliberate evidence gathering or verification that produces
findings or source-linked research notes before recommendations.

**Evidence gate**: The code decision (`evidence_gate.evaluate`) returning `allow`,
`must-refresh`, or `clarify-or-refuse`, plus per-work spoiler permission. It checks
finding freshness and certainty; agents still check taste sufficiency and fit.

**Consumption certainty**: Per-work `consumed`, `heard-of`, `unknown`, or
`won't-read`. Unlisted works are `unknown`. Only `consumed` and explicitly
`won't-read` permit spoilers; neither requires using them.

**Unread-safe**: Mood, theme and craft discussion without plot revelations for
works without spoiler permission.

**Taste cluster**: A distinct kind of enjoyment grounded in a user's own examples
and reasons. Several clusters may coexist without implying intermediate tastes.
