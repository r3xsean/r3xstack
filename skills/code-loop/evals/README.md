# code-loop regression suite

Past changes where code-loop missed a bug that someone later caught, replayed against code-loop's briefs as they are now. A run measures **reviewer and breaker detection and noise on these cases**, not code-loop's overall effectiveness: one sample per case, so a single changed verdict is a signal to look at, not proof.

## When to run

- Before and after an edit to code-loop's briefs (§1) or how findings are answered (§2), so the edit is judged against every case, not only the failure it answers.
- When the reviewer model `orchestrator_capabilities` resolves differs from the last run's model in `results.jsonl`.

## Run

1. `~/.agents/skills/code-loop/evals/run prepare --model <id> --effort <effort>`, with the model and effort resolved as code-loop §1 resolves the reviewer's. Add `--cases a,b` or `--roles reviewer` for a subset (skip the breaker when its brief didn't change), and `--skill <file>` to prepare the before run from the pre-edit text (for example `git -C ~/.agents show HEAD:skills/code-loop/SKILL.md`) when the edit is already made. It builds an isolated checkout per case holding only the candidate's history, writes each brief from SKILL.md's current text, and prints the briefs to start.
2. Start every printed brief as its own fresh `delegate_task` with that model and effort, the brief's text as the task, all in parallel. Pass the text, never the path: the run folder holds the answers.
3. Save each final reply, unedited, as `<case>.<role>.reply.md` beside its brief. A reply that errors or times out is restarted once; one that fails again is recorded as missed for every item, with that in `notes`.
4. Judge each reply against its `<case>.<role>.judge.md` and write `<case>.<role>.judgement.json`:
   `{"items": {"E1": "caught", "N1": "quiet"}, "other_should": 2, "notes": "..."}`
   - **expect items:** `caught` when a blocker or should (a reviewer) or a BROKE line (a breaker) names the same wrong outcome reached through the same code; `weak` when it is named only as a nit, a pre-existing finding or under Not verified / COULDN'T TEST; `missed` otherwise. Same failure means the same wrong outcome for the user, not the same file.
   - **noise items:** `raised` when the reply makes it a blocker or should; `quiet` otherwise.
   - **other_should:** the count of blockers and shoulds that match no item. Those are unjudged here; note any that look real in `notes`, since a new real catch is a new case.
5. `run report <dir>` checks every judgement, writes `results.md`, appends to `results.jsonl` and prints what changed since each case's last run. Then `run clean <dir>`.

Report the table and the changed verdicts. An edit that turns a `caught` into `missed`, or a `quiet` into `raised`, needs a reason before it lands.

## Add a case

From a problem caught after code-loop approved the change (a PR reviewer, the maintainer, the lessons log), once its pieces are reconstructed: the candidate revision code-loop approved, its base, the request as the author had it then, and the confirmed failure with its evidence. One JSON file in `cases/`, named by its `id`; copy an existing case's fields. Put declined findings from the same review under `noise` when the decline was argued with evidence. Never put the fix, a later design doc or the PR thread where the brief points: the request is copied into the run folder, but `setup` and `breaker_extra` paths are not, so they name only tools.
