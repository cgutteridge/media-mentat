---
name: setup
description: Start a private fiction taste record from book and DVD or Blu-ray shelf photos, then begin a focused taste interview. Use for new users without an established record.
---

# Photo-first setup

Apply the [main skill](../../SKILL.md) and establish the private workspace using
[workspace.md](../../references/workspace.md). Check for an existing profile before
creating anything. Never overwrite or reset an established record.

1. Begin by inviting photos of books/DVDs/Blu-rays or a small selection of
   favourites. Accept multiple photos over time. If the user cannot supply them or
   the host cannot inspect images, accept a typed list and continue.
2. Extract visible title, creator and medium into `taste/inventory.md`. Record
   image labels, identification confidence and ambiguous alternatives. Identify
   editions/adaptations separately when relevant. Confirm illegible identities
   before treating them as anchors; do not guess hidden spines or omnibus contents.
3. Create the blank record from `templates/grilling-record.md` using
   `scripts/init_workspace.py --workspace /absolute/private/workspace` when command
   execution is available. Otherwise create only missing files from the templates.
   Photos remain private and need not be copied from the host or retained.
4. Ask one question about ownership and experience: which visible works belong to
   them and which have they actually read/watched? A gift, unread purchase,
   household member's book, or disliked work is not positive taste evidence.
   Store confirmed consumption per work in the Consumption certainty table;
   uncertain identifications remain inventory observations.
5. Follow the [interview subskill](../interview/SKILL.md), starting with a confirmed
   favourite and what they like about it. Contrast with another familiar work
   when useful. Explore distinct kinds of enjoyment before summarising tastes.

Setup is usable once a private record exists, at least one confirmed anchor has a
user-stated reason, and essential constraints for the requested recommendation
are known. Label the profile provisional when breadth is still limited; research
and deliver a narrow initial pass rather than inventing a complete personality.
Continue learning from feedback. Never import a previous user's tastes.
