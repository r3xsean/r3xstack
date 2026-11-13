---
name: writing-steering-files
description: Create or edit a steering file — a skill, an AGENTS.md/CLAUDE.md, or a durable agent prompt — through a grill-and-distill loop. Use whenever writing a new skill, AGENTS.md, automation prompt, or product system prompt, changing an existing one, or when another skill needs a steering file authored.
---

A steering file (a skill, an AGENTS.md/CLAUDE.md, a durable agent prompt) encodes behaviour for future agent sessions. The human must end every run knowing exactly how the file is structured and what behaviour each part encodes. They approve the plan in distillations — intents and shape, before any text exists — and the result in its real text: wording is what steers, and a distillation written by the drafter smooths over exactly the bloat and drift a review should catch. Outside the walkthrough, answer questions about how something works with a distillation, going deeper on demand.

## Branches

Eight ways in; all run the same loop, scoped differently:

- **Create a skill** / **Create an AGENTS.md** / **Create an automation prompt** / **Create a product prompt** — grill and shape the whole file.
- **Edit a skill** / **Edit an AGENTS.md** / **Edit an automation prompt** / **Edit a product prompt** — grill and shape **only the delta**. The existing file is context to read and respect, not material to re-litigate; leave approved behaviour alone unless the delta forces a conflict (then surface the conflict, step 2).

An **automation prompt** runs unattended with no human in the session; a **product prompt** is the system prompt behind a feature other people use.

Each branch has exactly one craft file: [`skill-craft.md`](skill-craft.md), [`agents-md-craft.md`](agents-md-craft.md), [`automation-prompt-craft.md`](automation-prompt-craft.md), [`product-prompt-craft.md`](product-prompt-craft.md). The shared principles at the bottom of this file apply to every branch.

## The loop

Scope, grill, and shape go to the human as one message when none of them waits on an answer to another; each still needs its approval. That message also names each step 5 run that applies and what it does, so the human approves runs with the plan — all, some, or none. A run that only becomes relevant later is asked for when it does.

### 1. Scope

Name the branch (create/edit × skill/AGENTS.md/automation prompt/product prompt) and state the target in one line: which file, and what behaviour change the run exists to produce. For edits, read the existing file first and restate the delta as "currently the agent does X; after this edit it should do Y." When the edit answers an observed misbehaviour, name what produces X — see *Root cause first*.

**Then read the branch's craft file, in full, before grilling** — the grill's branch-specific checks come from it, and the draft is judged against it. One craft file per run; never more than one.

Done when the human confirms the scope line.

### 2. Grill

No file writing yet. Convert every candidate rule into a **behavioural intent**: "given [situation], the agent should [observable behaviour]." A rule that can't be stated this way is steering nothing — challenge it or drop it. Then attack the list:

- What's ambiguous — would two reasonable agents act differently under this wording of the intent?
- Is it a no-op — would a capable agent already do this without the rule?
- Does it overreach — what legitimate request would this wording block or bend? Look for a forced method, a closed list of answers, a ban written just in case, and a question framed around a conclusion.
- Does it belong here — or in another steering file that is already this meaning's single home?
- **Edits only:** does the delta contradict or duplicate anything already in the file? Name the collision and propose replace-or-remove; never layer a new rule over a stale one.
- **Skills only:** settle invocation (model-invoked, phrase-triggered, or user-invoked), the leading word if one exists, and what belongs behind a script versus in prose.
- **Automation prompts only:** settle what belongs in the prompt versus a skill the run already loads, and what the run may write.
- **Product prompts only:** state each intent as a situation a real user could create, so it can become a probe in step 5.

Done when the human approves the intent list. For edits, that list covers only the delta.

### 3. Shape

Propose the structure **distilled**, before drafting any full text: each section in one line — what it holds, which intent it serves, and whether it sits in-file or behind a pointer. For skills, include the frontmatter description verbatim (it is short, and it is the trigger). For edits, show where the delta lands in the existing structure, what gets replaced or removed, and whether it forces restructuring.

Iterate with the human on the shape. Done when the human approves it.

### 4. Draft

Write the file(s), applying the branch's craft file and the shared principles below. Every intent from the grill maps to a specific section, and no section exists without an intent behind it. Done when the file is written and the mapping is complete — an intent with no home, or a section with no intent, is an unfinished draft.

### 5. Probe

Four cases, each a subagent run that takes real time. Run only what the human approved, and skip the step when nothing was. In later rounds, offer a rerun only for what the round changed, and run it only if approved.

- **Product prompts.** Derive a probe from each intent, run them against the real feature, and triage what comes back to the surface that owns it — see [`product-prompt-craft.md`](product-prompt-craft.md). Done when every intent has been probed and each one passes or has its failure surfaced in the walkthrough.
- **Regression suite.** When the edited skill has one (an `evals/README.md`, as `code-loop` has) and the edit touches what that README says to run it for, run it before and after the edit as the README says, first adding as a case any observed failure the edit answers. Done when both runs are reported with every changed verdict.
- **Observed failures.** When the edit answers an observed failure no suite holds and its original prompt and context are still available, replay it: a fresh subagent given the edited file and the original prompt, nothing from this session. Report the result as one replay — a smoke test, not proof. Done when every replayable trigger has been replayed and reported.
- **Cold run — AGENTS.md, automation prompts, and skills.** Once the draft is on disk, a fresh subagent meets it with nothing from this session and reports where it had to guess; the branch's craft file defines its task and its report. Fix each finding in the file, or record it in the walkthrough as a fair judgement call. Done when every finding is triaged.

### 6. Walkthrough

Lead with the distillation: per section, the intent it encodes plus every judgement call made while drafting — any deviation from the approved shape, and any wording choice that strengthens, weakens, or scopes a rule differently than the grill agreed. Then show the real text. The first walkthrough of a run shows every file of the steering file in full, with the run's changes marked — a whole-file diff, not hunks — so the human can also spot older lines that no longer earn their place. Later rounds show only what changed since the previous walkthrough, as diffs with enough surrounding lines to read each change in place; keep a copy of the files from before the first edit and as each walkthrough showed them, outside the steering file's folder, as each round's base, and delete every copy and diff output when the run ends. Head each with its size against that same base: words before and after per changed file, lines added and removed, and a flag if the edit only adds. For edits, the distillation covers only the changed sections and confirms in one line that the rest is untouched. Where step 5 ran, cover what it changed and why. Requested changes loop back through shape or draft, whichever they touch.

Done when the human approves the walkthrough — meaning they hold the file's structure and behaviour and have seen the words that carry it.

## Principles for every steering file

These bind every branch; the craft files add only what's specific to theirs.

- **Predictability is the root virtue.** A steering file exists to make future agent behaviour predictable — the same *process* every run, not the same output. Every principle below is a lever on it.
- **The no-op pass.** Judge every sentence by the removal test: what would a capable agent concretely do differently because it exists? A sentence earns its place when it changes an action, branch, boundary, artifact, or completion judgement; a "why" earns its place only when it prevents a plausible misapplication. Two forms always fail: the default restatement (asking for what competent execution already does) and the ungrounded quality exhortation (*be thorough*, *use good judgement*) — replace with the missing scope, threshold, or decision rule; if none exists, delete. The grill's behavioural-intent test is this principle applied before drafting.
- **Single source of truth.** Each meaning lives in exactly one authoritative place, so changing a behaviour is a one-place edit. Duplication costs maintenance and tokens, and inflates a meaning's prominence past its real rank.
- **Relevance and sediment.** A line loses relevance by never bearing on behaviour, or by going stale as the file's world changes. Sediment — stale layers accumulating because adding feels safe and removing feels risky — is the default fate of any steering file without a pruning discipline: every edit prunes as well as adds, and an edit that only adds is suspect.
- **Root cause first.** When a steering file misbehaves, the cause is often its own text — a line pointing the agent at the wrong tool, a rule broader than its failure — or a surface beside it. Before writing a fix, name what produced the behaviour; when the misbehaving session is still reachable, ask it why it acted. Then fix in order: rewrite or delete the line that caused it; move the rule into a mechanism, so a tool, its output, or a script makes it unnecessary; only then add a rule.
- **Sprawl.** Length is a cost even when every line is live and unique — the agent wades through more before acting, and attention thins across the excess. Cure it by disclosure and splitting, never by tolerating it.
- **Progressive disclosure.** Three tiers: the always-loaded top; reference behind context pointers, loaded when a condition fires; and the **decision point** — a tool's description or output, a script's result, an error message — read at the moment the choice is made. Inline what every run needs; disclose what only some runs reach; when a rule governs what to do after a tool or script runs and the author owns that surface, put the rule there. A pointer's *wording* — stating when to read the target, not just that it exists — decides when and how reliably the agent gets there; if must-have material sits behind a weak pointer, sharpen the wording first and inline only if that fails.
- **Co-location.** Keep a concept's definition, rules, and caveats under one heading, so reading one part brings its neighbours with it. Scattering fragments one meaning across many places — distinct from duplication, which repeats it.
- **Grants.** Where a model's default refuses, asks first, or hedges on an action the author wants — merging, force-pushing with a lease, running tests without asking — the file states the permission, its bound, and what stays outside it. Write one when a run has been seen stalling on the action, or the author asks; never speculatively.
- **Intent over method.** Give the situation, what's wanted back and the limits, and leave the route to the agent. A constraint on how it works is written as a grant is: when a run has been seen going wrong, or the author asks; never just in case. So leave open the steps of a judgement and the form of its answer, say in specific words what the agent is free to do, and name "nothing" as a full answer where it is one. Keep exact: limits on actions, what a step must deliver and when it is done, whatever a script or another agent reads, and a scope and stopping point for a model seen to keep adding.
- **Leading words.** A compact concept already in the model's pretraining (*lesson*, *tracer bullets*, *fog of war*), repeated as a token, anchors a whole region of behaviour in the fewest tokens by recruiting priors the model already holds. It must compress a behavioural concept, not intensify a virtue — replacing *thorough* with *relentless* still says only "do more" and stays a no-op. The same word used across prompts, docs, and files links them all to the same behaviour.
