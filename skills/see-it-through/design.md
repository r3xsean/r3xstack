# Design

Read at step 3 of [SKILL.md](SKILL.md), before choosing an approach.

## Ground the change

Name, from the code: the owner of the behaviour, where its authoritative state lives, every caller and every writer of that state, the contracts they rely on, and whether the change would make a decision already made elsewhere. In a light run this is a few `file:line` references and a sentence. When the change moves ownership or a boundary, first find why it is shaped this way today, from history, docs or comments.

Check the destination's commits since your base and open work on the same behaviour, others' and your own. Say in the explainer what you found and what you'll do: for work that already delivers the change, a reassessed approach; for work that alters behaviour the change relies on, an order to agree with that work's author or a test of the affected behaviour on a combined tree before shipping.

For a bug, once it reproduces, decide whether the state that causes it is legitimate: handle a legitimate state where it enters the system, and fix whatever produces an illegitimate one.

Weigh what the change costs, its code, tests, harness, review and upkeep, against who hits the problem, how often, and the harm when they do. Verify coverage is the exception: judge it by whether the flow will be checked again, not by this change's reach. Choose the smallest approach that settles it, and when even that costs more than the problem does, recommend a smaller version or no change in the explainer; the user decides. In the back-and-forth, give the model your reach and cost estimate, and weigh a smaller version or no change among the alternatives.

## The structural question

Ask it every run: could the existing owner or API express this change cleanly, and would removing or reshaping something solve it more directly than adding to it? "The existing structure fits" is a valid answer; say why.

Weigh the smallest patch against a structural option in the back-and-forth when the change:

- creates or moves ownership of state;
- adds a public API;
- makes a decision already made elsewhere;
- adds a layer;
- or works around what an earlier workaround already worked around.

Compare them on what callers must do, who owns what, compatibility, how each is verified, and migration cost. The structural option doesn't win for looking cleaner.

## Shape

- A new API starts from its callers: sketch representative calls, failure behaviour, ownership and, where it applies, cancellation, before signatures.
- Use types to make an invalid state unrepresentable or to parse data once where it enters, when that removes repeated checks; not types that need casts to get around.
- When the design sets a boundary later changes must respect, enforce it with types, module exports or an import rule where the repo allows, and write the reason for a non-obvious ownership decision in the repo's AGENTS.md.

## Order

When the structural change can keep the current contract and makes the behaviour change easier to review, it goes first: a check through the repo's verify skill pins the current behaviour, the reshape keeps it passing, then the behaviour change lands on top. When the two can't be separated, say so in the explainer and prove both the new behaviour and the contracts kept.

Remove only complexity the change touches. Migrate internal callers and delete the old API in the same change; a public API or an independently deployed consumer gets a migration plan in the explainer instead.

## A repo the user doesn't own

A structural correction the approved change needs is in scope. Wider cleanup, a changed approach and refactors raised by the lessons log are proposals to the maintainer, never scope the change takes on.
