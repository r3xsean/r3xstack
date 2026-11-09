# AGENTS.md craft — what only AGENTS.md files have

Disclosed reference for [`writing-steering-files`](SKILL.md), read in full on the **AGENTS.md branches** after Scope. The principles shared by every steering file live in `SKILL.md`; this file covers only what is specific to AGENTS.md.

An AGENTS.md differs from a skill in one structural fact: it is loaded into **every** session in its scope, unconditionally. There is no invocation decision and no trigger to tune — every line is context load paid on every future turn of every future session. Three consequences follow directly:

- The pruning bar is the highest of any steering file, and sediment is costlier here than anywhere else — an edit that only adds deserves extra suspicion.
- The root file is the always-loaded tier of the disclosure ladder: keep it short, push anything situational behind a condition-worded pointer ("touching the payment flow → read `docs/payments.md` first"). A root file that is mostly a router with well-worded pointers scales indefinitely; one that holds everything sprawls.
- The file's job is precise: onboarding doc and standing orders for a cold-start agent, nothing else.

## Steer toward outcomes, not locations

A file that lists where things live ("components are in `src/components`, API routes in `src/api`") is a map, not steering — a capable agent finds structure by looking. Every line should change what the agent *does*: a rule, a constraint, a threshold, a command, a decision procedure. Locations earn a place only when they are non-obvious *and* load-bearing (a build artefact directory that must never be edited; a specs directory the workflow depends on).

The failure mode is the **map-file**. Symptom: an agent behaves identically with the file deleted. Cure: rewrite each line as a behavioural intent or cut it.

## The cold-start test

Write for an agent with zero conversation history. If correct behaviour still depends on something the humans "just know," the file is incomplete — that knowledge is exactly what belongs here.

The cold run (`SKILL.md`, step 5) checks it. The task is one line drawn from the repo's recent history, such as a recently merged PR's title. The subagent edits nothing, works out the task end to end — what it would change, which commands it would run to check it, when it would call it done — and reports only: its guesses, where it chose between options nothing settled; facts it needed that reading the code couldn't give it (commands, conventions, places it must not touch); and what it would have stopped to ask. It quotes the file's line where one applies. Structure the code shows is not a finding — see *Steer toward outcomes, not locations*.

## A glossary is a terminology contract

When rules lean on a term with more than one plausible referent, or the file must distinguish parties — maintainers, the end user, the agent itself — define each term once in a short glossary and write every rule in that vocabulary. The threshold is genuine ambiguity: a file whose terms each have one obvious referent needs no glossary. Distinct from a leading word (`SKILL.md`): a leading word recruits a prior the model already holds; a glossary pins project-local vocabulary that has none. During the grill, flag any candidate rule whose wording depends on an undefined term.

## The dominant defect

Most repos have one dominant way changes turn out incomplete. When it can be evidenced, encode it as a done-gate: a short checklist the agent walks before calling work done, **stating which entries applied** — attestation, not silent holding. Attestation costs tokens every run; the dominant defect earns it, ordinary rules do not.

Source the initial list from structure, not anyone's recall: inspect the repo for parallel surfaces a change can silently miss — sibling clients, per-provider adapters, locales, reverse states (every way in needs a way out). What the architecture forces belongs on the list; a guessed entry is aspiration.

Then make the list a living one: write a standing promotion rule into the file — when the human corrects a missed case ("you also needed to handle X", "same for anything like this"), the agent proposes promoting that class of miss into the checklist while the correction is live. The checklist grows from real corrections; the human only approves promotions.

## Encode pushback

Steering is not only toward correct action but away from known failure — one of the file's highest-leverage uses. Three kinds of away-steering, each a standing order:

- **Declining requests.** Recurring requests that should be refused, tempting shortcuts that have burned the project before, changes that need explicit sign-off: "if asked to X, stop and say why not."
- **Dangerous operations.** Where the operating context makes a normally-safe action destructive — the agent runs inside the product it is editing, live user data sits beside test data, other dev servers share the machine — establish those facts from the repo and the machine first, ask only what can't be observed, then name each action alongside its safe alternative ("kill only a PID you captured at spawn"). A prohibition without an alternative just relocates the improvisation.
- **Calibration downward.** Where the agent's trained default does too much for this project — over-flagging security, unrequested browser verification, repo-wide checks — encode the do-less rule with its explicit boundary ("no repo-wide checks unless asked"), never as a tone request ("don't over-index"). Write one when a run has been seen overshooting, or the author asks; never speculatively.

## Actual practice, not aspiration

Every rule must describe how work actually happens, not how anyone wishes it did. An aspirational rule is worse than no rule: the agent will enforce it against its own author, and the author will override it every session — teaching the agent (and every future reader) that the file is negotiable.

The failure mode is **aspiration drift**. Symptom: the same rule overridden across sessions. Cure: make the file match reality, or change reality first — never leave the gap standing.

That cure is edit-time; conflicts also need a run-time protocol, declared in the file itself: the developer's explicit instructions outrank it, and when a rule fights the task in front of the agent, it says so loudly and gets sign-off before breaking it — never silently folds, never enforces the rule against its own author. Without the declaration, two reasonable agents diverge on the same conflict, one rigid and one folding.

## Placement across the file ecosystem

A rule lives in exactly one steering file. Between the candidates — root AGENTS.md, a nested AGENTS.md deeper in the tree, a linked doc, a skill — place it in the narrowest scope that covers every session needing it, and make other files point rather than restate.

Keep one canonical agent-context file (AGENTS.md) and make tool-specific files delegate to it — a CLAUDE.md containing `Read @AGENTS.md` and nothing else. Two parallel context files drift; a pointer cannot.
