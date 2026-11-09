# Council

Scored review rounds on fresh screenshots, compared against competitor apps, in batches of five rounds. After each batch the user decides whether it continues.

**When:** for new UI, once the user says the look is settled; for existing UI, from the start. Never on exploration directions.

**Set up once per run**, in `run.md`:
- the members (SKILL.md);
- the competitor captures (harness-contract.md);
- the target: every member scores every screen at least 9 and above every competitor, unless the user set another target.

## A round

1. **Capture** every scenario, viewport and flow fresh. Fix failed cases, or list them as missing.
2. **Build the pack** in a new folder outside the repo, holding only:
   - our captures and the competitor captures, each competitor file named after the pattern it shows;
   - copies of the product brief and `references/craft.md`;
   - `decisions.md`: DESIGN.md's decisions and exceptions, each with its rule, scope and where it applies (no basis lines, never the reaction log);
   - `brief.md`, filled from `templates/council-brief.md`.

   Leave out manifests, `run.md`, earlier scores and findings, member names, and anything showing personal data.
3. **Start every member in parallel**, each a fresh read-only delegated task with its model and effort from `run.md` (in T3 Code, `delegate_task`). The task is only: "Read-only design review. Read `<pack>/brief.md` and follow it. You may read every file inside `<pack>/` and nothing outside it."
4. **Merge** the replies into the findings ledger: one row per distinct problem, with its files, which members raised it, severity, and status. For a high or medium finding raised by one member only, look at the cited captures yourself and mark it `verified` or `rejected`, with a one-line reason.
5. **Act on each finding** that is verified or was raised by more than one member. First check the finding and its remedy against `decisions.md` and the brief's copy rules.
   - **Fix:** execution problems, such as alignment, type, radii, contrast, clipping, overlap, truncation, wrong or inconsistent numbers, or a broken state. Make the smallest change.
   - **Skip:** the finding or its remedy contradicts a decision or exception. Mark it `rejected — decision` and change nothing. If it shows the decision blocking a task, put it in the checkpoint report.
   - **Hold:** the remedy changes something the user hasn't decided and carries a real tradeoff, such as adding explanatory text, or changing density, colour, layout or hierarchy. Mark it `held` and change nothing. Routine repairs (a missing unit, overlap) are never held.
6. **Add a row to the score table** in `run.md`: the round, then each member's scores per screen and viewport, with their competitor scores.
7. **Stop the batch early** when the target is met; otherwise run the next round, up to five per batch.

A reaction from the user at any point is recorded, wins over the council, and is applied before the next round.

## Checkpoint

After five rounds, or as soon as the target is met, stop and report to the user:
- the score table across all rounds;
- what was fixed;
- each held item, with its finding and the options;
- each decision that blocked a task;
- the findings still open.

The user decides: run another batch of five, apply or decline the held items, or stop. Never start another batch without their yes. When the work ends in a pull request, put the score table in its description.

Done, per batch, when the checkpoint report is delivered.
