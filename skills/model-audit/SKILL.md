---
name: model-audit
description: Use when the user says "audit the models" in a workflow, or another skill hands over a model launch.
---

Decide which model and effort each role in a workflow runs on, from what the plans actually charge and what the evidence shows, and change only what those roles touch. Two ways in: a model has launched (which roles, if any, should it take?), or the user names a workflow (do its roles fit?).

The target is the user's own workflow (their skills, their AGENTS.md and what they type to start a run) or one named automation. Audit both in one run only when the user asks.

The other model is the newest model, in `orchestrator_capabilities`, of the family the user named, at the effort they named. It is the partner for step 8's debate, not a candidate for any role. If the family or effort is missing, ask for it and do nothing else until they answer.

## 1. Terms

Read the target's last entry in its log (step 10) and reuse what still holds; no entry means a first run. Then ask, in one message, for whatever the request and that entry don't settle: the efforts allowed, what the budget is for (hold today's rate, fill the plan, or a cap), whether roles must stay the same between resets, and how much of the plan this audit may spend.

Done when each of the four is answered or carried over from the log.

## 2. Inventory

List every role: what it does, the model and effort it resolves to today (the exact model id, since a family name moves when a model launches), where that is set, the text it is given, the working directory its launcher gives its sessions (their records are filed under it), and which plan or key pays for it. Run `python scripts/inventory.py <workflow root>` from this skill's folder for the lines that set a model and for what the sessions recorded; trace by hand every value it marks, and every default it can't see. For an unattended role, add what it does when the plan runs out: waits, fails where someone will see, falls back, or spends credits.

Done when every role has its row, or is marked unresolved with what stopped you.

## 3. Measure

Run `python scripts/meter.py` for what 1% of each plan's limit costs per model, and how full each plan is. It reads one machine and the providers it knows: for each machine or provider it lists as not seen, run it there or say the figure leaves it out. A plan can have more than one meter, such as a sub-limit that counts only some models: name the meter each role draws on. From the session records, give the target's share of each plan.

Never price a recipe on API prices alone. When a rate that could reverse the choice has no clean measurement, run one real task on that model at that effort with nothing else running, and measure again; when that can't be done, mark every recipe that leans on it provisional.

Done when each model in play has a measured rate on its plan, or is marked unmeasured.

## 4. Evidence

For a launch: the launch post, the capability and behaviour sections of its system card, and the vendor's prompting and migration guides, read in full, with scores taken at the efforts in play, not at the effort the vendor leads with. For a workflow: its recorded runs, with their outcomes, retries and failures. For both: independent results for each candidate model at those efforts, saying what each result measures and who ran it.

When two models score alike, expect the bigger one to do better in practice. Weigh results that are hard to tune for (breadth of knowledge, private or rebuilt task sets, human grading) above the rest.

Done when each candidate model and effort has its evidence, or is marked as having none.

## 5. Recipes

Present a few recipes, with no change and the ones over a limit among them. Each gives every role its model and effort, and its expected use of every plan it draws on: the total, the part per model, and the estimates it rests on, each marked measured or guessed. For an automation, count retries and failed runs in the cost of a successful result. The user picks.

Done when the user has picked a recipe.

## 6. What the choice touches

In scope: for each role whose model or effort changes, the text it reads, the handoffs into and out of it, and any instruction it shares with other roles. Check a shared instruction against the roles that didn't change before editing it. Nothing else is in scope: a launch is no reason to clean up the rest.

Within scope, a line goes when it covered a weakness of the model that left the role, repeats another line, describes mechanics that no longer exist, or conflicts with something you can show. A line with no recorded reason stays unless one of those holds.

Done when each change is listed with its file, and each role that didn't change has nothing listed against it.

## 7. Test

Run the smallest tests that could change the choice. A role with a regression suite gets it rerun (`code-loop`'s, when the reviewer or breaker changes). An automation gets recorded inputs replayed on the candidate with publishing and writes off, compared on outcome and on cost per successful result.

Done when each test has run and its result is reported, failures included, or the reason none applies is stated.

## 8. Debate

Go back and forth with the model (the `back-and-forth` skill) on the picked recipe and the changes it needs, with the inventory, the measurements and the evidence in the Context.

Done when the back-and-forth concludes.

## 9. Change

Each change takes the route its file has: a steering file through the `writing-steering-files` skill; code and configuration through the `see-it-through` skill in that repo. What an unattended role does when the plan runs out is set in its configuration, never in its prompt.

Auditing the user's own workflow, list each automation that pins a model the choice affects as a follow-up; don't change it.

Done when each change is made and approved by its route, or listed as approved and not yet made.

## 10. Log

Append a dated entry: for the user's own workflow, to `~/.agents/models/log.md`; for an automation, in its repo, where it already keeps decisions or else in a `MODELS.md` beside the workflow, with nothing personal in it. The entry holds the target; each role's model, effort and exact id, with any condition on it; where each is set, and at which revision; the measured rates and how they were measured; why the recipe won and what lost; what is approved and not yet made; and what is still unmeasured. Raw records stay out of the log and out of this skill's folder.

Done when the entry is written.
