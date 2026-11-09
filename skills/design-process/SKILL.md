---
name: design-process
description: Use when designing, redesigning or polishing a product's UI; when running a design council on screenshots; or when recording the user's reactions to designs.
---

# Design process

The user decides direction and taste. Models judge execution: can the task be done, are the numbers true, does anything break, hide or mislead. A score, a council or model consensus never chooses between directions, merges them, or overrules a recorded decision.

If the project has its own design skill, follow it; it may send you back here for a phase.

## The project's files

In `docs/design/`, unless the project's AGENTS.md names another place for these files:

- `product-brief.md`: product truth. Who uses it, what each surface must let them do (its leading question and mode: Operate, Read or Persuade), data and states, copy and trust boundaries. If the project already has a `PRODUCT.md`, the brief links to it instead of repeating it.
- `DESIGN.md`: the user's decisions, exceptions, approved reference screens and the reaction log. A recorded decision wins over your preference. Where none is recorded, the look is open; the current UI is evidence, not a decision.
- `harness.md`: how screens and prototypes run and get captured: commands, scenarios, viewports, the competitor apps, where captures go.
- `runs/<YYYY-MM-DD-name>/run.md`: one run's question, what is fixed and open, known limits, council members and target, the stance key, the outcome.

Templates for all four are in `templates/`. If any of the first three files is missing, bootstrap first. Every run, including one that skips bootstrap, starts its own `run.md`. Captures, manifests, findings ledgers and variant sheets go in the gitignored folder `harness.md` names. Council packs go outside the repo, in the session's scratchpad or temp folder.

The project's own rules win over this skill: its AGENTS.md on dependencies, dev servers and what gets committed. When the run needs something those rules forbid or reserve for discussion, ask the user before doing it.

## Flow

- **New UI:** bootstrap → explore → the user picks → refine → council → approve a reference → holdout → ship through the project's rollout path.
- **Existing UI:** bootstrap → council → approve → ship. When the user wants visible changes first, refine before the council.

Enter at the phase the request names; a narrow tweak enters at refine.

| Phase | Read first |
|---|---|
| Bootstrap | [references/bootstrap.md](references/bootstrap.md), then [references/harness-contract.md](references/harness-contract.md) for each capability the run needs |
| Explore | [references/explore.md](references/explore.md) |
| Refine | [references/refine.md](references/refine.md), and [references/craft.md](references/craft.md) before the first UI edit |
| Council | [references/council.md](references/council.md) |
| Using another design skill | [references/integrations.md](references/integrations.md), before invoking it |

**Council members.** When the run will reach the council, ask the user at the start who sits on it (each member's model and reasoning effort), unless they already named them. Suggest members from different providers. Record the members in `run.md` and use exactly those for the whole run. If a member is unavailable, say so; never substitute one.

**Approve a reference.** Only the user's words approve a screen; scores never stand in. Copy its captures to `docs/design/references/` and list them under Reference screens in DESIGN.md, saying what each is the reference for.

**Holdout.** After the first approved reference, a fresh agent designs a surface that has not been designed yet, from this skill, the project's files and the harness alone, and lists every point where it had to guess. Show the user the result. Fix each guess in the file that should have answered it, or record it in `run.md` as open. Done when the user has reacted and every guess is fixed or recorded.

## Record reactions

Whenever the user reacts to a design, in any phase:

1. Add one row to DESIGN.md's reaction log per reaction: date (UTC), surface and viewport, which design and capture run, the user's words quoted exactly, type, scope, status `observed`.
   - **Type:** `like` (keep it), `dislike` (change it) or `defect` (a task failed or something broke; also add it to the findings ledger). One reaction can like one part and dislike another; name each part. A feature not built yet is not a reaction: list it under known limits in `run.md`.
   - **Scope** is what the user stated: this element, this surface type, or site-wide. If they stated none, it is the element. Never widen it yourself.
   - What you changed in response goes in the findings ledger, not in the row.
2. Promote a row into Decisions when the user states it generally. When the same reaction recurs on a second surface, ask whether it applies generally and promote only on yes. Mark the row `promoted` with a link.
3. When a reaction contradicts a decision, ask which wins, then edit or remove the old decision and mark the losing rows `superseded`.

Done when every reaction has a row and every promotion cites the user's general statement or their yes.

## Privacy

Captures use fixture data, seed data or a demo account, never the user's own account or real people's records. Nothing showing personal data or adult content goes into a council pack, a reference capture or a commit.
