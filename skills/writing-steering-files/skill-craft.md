# Skill craft — what only skills have

Disclosed reference for [`writing-steering-files`](SKILL.md), read in full on the **skill branches** after Scope. The principles shared by every steering file — predictability, the no-op pass, single source of truth, sediment, root cause first, sprawl, disclosure, co-location, grants, leading words — live in `SKILL.md`; this file covers only what skills have and AGENTS.md files don't: an invocation decision, a description, steps, and scripts.

## Invocation

Three choices, trading different loads:

- A **model-invoked** skill keeps its `description`, so the agent can fire it autonomously — and other skills can reach it. There is no model-only state: a description only ever *adds* agent discovery on top of the human's ability to type its name. The cost is **context load**: the description sits in the window every turn, spending tokens and attention permanently.
- A **phrase-triggered** skill is model-invoked with a description that is only its trigger — "Use when the user says *full send*", plus any reach clause another skill needs. Context load shrinks to one line, it still fires only when the phrase appears, and unlike user-invoked skills several can fire from one prompt or one spoken sentence. If it grants authority, the body opens by confirming the phrase was actually said, falling back to ordinary behaviour when it wasn't — a misfire must not hand out the grant.
- A **user-invoked** skill sets `disable-model-invocation: true`, stripping the description from the agent's reach: only the human, typing its name, can invoke it — and because nothing agent-visible names it, no other skill can fire it either. Zero context load, but it spends **cognitive load**: the human is the index that must remember it exists and when to reach for it. Cognitive load is not a cost to minimise — it is the price of human agency; spend it where human judgement matters, remove it where it doesn't.

Pick model-invocation when the agent must reach the skill on its own, or another skill must. If it only ever fires by hand, make it phrase-triggered when it combines with other skills or gets said aloud, and user-invoked when zero context load, or a guarantee it never fires unasked, is worth the human remembering it.

When user-invoked skills multiply past what the human can remember, the cure is a **router skill**: one user-invoked skill that names the others and when to reach for each. It can only hint, never fire them — user-invoked skills have no description, so nothing but the human can reach them.

## Writing the description

A model-invoked description does two jobs — state what the skill is, and list the **branches** that should trigger it (a branch is a distinct way the skill is invoked; different runs taking different paths through it). Every word is permanent context load, so a description earns even harder pruning than the body:

- **Front-load the skill's leading word** — the description is where it does its invocation work, and when the same word lives in the human's prompts and docs, the agent links that shared language to the skill and fires it more reliably.
- **One trigger per branch.** Synonyms that rename a single branch are duplication — collapse them; keep only genuinely distinct branches.
- **Cut identity that's already in the body.** Keep the description to triggers, plus any "when another skill needs…" reach clause.
- For a phrase-triggered skill the description is the trigger phrase alone, plus any reach clause. The phrase is its leading word, so use the words the human actually says.
- For a user-invoked skill the description becomes human-facing: a one-line summary, trigger lists stripped.

## Mechanism boundary

Before arranging or pruning prose, draw the line between agent-visible control and deterministic implementation:

- Keep in `SKILL.md`: judgement, user intent, authorization, interpretation, genuine choices, the entry point, the artifact contract, and user-actionable blockers.
- Put behind a bundled script: deterministic, repeatable mechanics — prerequisite setup, safe retries, fallback selection, conversion, caching, cleanup, output formatting. Keep an action agent-visible only when it needs new authority or context-dependent judgement.
- Put facts or conditional guidance the agent may reason with in reference; delete prose that merely narrates the hidden implementation.

For a deterministic tool wrapper, default to a thin control plane: trigger in the description; entry point, genuine options, result contract, and user-actionable blockers in the body. Let the entry point own setup and internal branches, and keep tool output bounded by writing large results to artifacts and returning their locations.

**Leaky mechanism** is the failure mode: deterministic implementation details escaping into agent instructions. These can be relevant, unique, and behaviour-changing, so the ordinary no-op pass does not catch them — a sentence can change behaviour and still be leaky. The cure is executable encapsulation, not moving the prose behind a pointer: make the entry point own the mechanics, leaving only genuine decisions and observable contracts in `SKILL.md`.

## Steps and completion

A skill's prose is **steps** (ordered actions, the primary tier when present) and **reference** (consulted on demand). A skill can be all steps, all reference, or both — a flat peer-set of rules with no steps is a fine arrangement, not a smell. When a skill has steps, in-file reference that should be disclosed buries them and turns attending to them into a coin-flip.

Every step ends on a **completion criterion** — the condition that tells the agent the work is done. Two properties make it a lever:

- **Clarity** (can the agent tell done from not-done?) resists **premature completion** — ending a step early because attention slips to *being done*. A vague bound ("understanding reached") gives way; a sharp, checkable one holds.
- **Demand** (how much it requires) sets **legwork** — the digging the agent does within the work. "Every modified model accounted for" forces thorough work where "produce a change list" does not. Demand binds flat reference too: "every rule applied" is how a skill with no steps still carries an exhaustiveness bar. Quality adjectives (*comprehensive*, *thorough*) set no demand without a scope or stopping condition.

When a script owns the internals, set the criterion at its observable artifact boundary rather than restating its internal sequence as agent steps.

Premature completion is a tug-of-war: visible **post-completion steps** (the steps still ahead) pull the agent forward; the criterion's clarity resists. Defend in order: **sharpen the bound first** — cheap and local. Only when the criterion is irreducibly fuzzy *and* the rush is actually observed, hide the later steps by splitting the sequence — and hiding only works across a real context boundary (a user-invoked hand-off or a subagent dispatch); an inline call leaves the later steps in context and clears nothing.

## Unwatched runs

Some skills run on after the human stops watching, though they can still be reached — "full send" hands off a change to land on its own. Unlike an automation prompt, there is someone to ask; like one, a question in an ordinary message goes unread and the session looks finished. Such a skill says:

- Ask only through the harness's question tool, so the session visibly waits, and put the context, the blocker, and the recommended option first in the question itself.
- Ask only on named blockers, listed in the skill (can't be proven, outside the grant, goal ambiguous); everything else proceeds.
- With no question tool, or no answer, stop without taking the blocked action and lead the final message with the question.

## When to split

**Granularity** is how finely skills are divided, and each cut spends one of the two loads, so split only when the cut earns it:

- **By invocation** — split off a model-invoked skill when a distinct leading word should trigger it on its own, or another skill must reach it. The new always-loaded description is the price; independent reach has to be worth it.
- **By sequence** — split a run of steps when the post-completion steps tempt the agent to rush the one in front. Beware the reverse: merging sequences exposes each step's later steps to what follows, inviting premature completion.

## Black-box test

The skill's cold run (`SKILL.md`, step 5). A fresh subagent invokes the skill from its primary invocation on a realistic task, as a dry run: it does every read, runs only read-only commands, and makes no writes, pushes, merges, comments, or messages, listing each write it would have made instead. When a skill can't be meaningfully dry-run, say so and offer no run. A tool-backed skill passes when the agent reaches the promised artifact (in the dry run, the point of producing it) from the documented entry point without improvising deterministic setup or internal branches — only genuine choices and user-actionable blockers escape the mechanism — with tool output bounded and completion observable at the artifact boundary. A failure here is a mechanism-boundary defect: repair the mechanism before adding prose.
