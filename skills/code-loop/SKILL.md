---
name: code-loop
description: Use when the user says "code loop with" a model, or another skill asks for a code loop.
---

Review a code change with another model in up to 3 rounds: a reviewer reads the change, and a breaker tries to break it with tests. Keep each fix the smallest that resolves its finding, and push back with evidence when a finding is wrong.

## 1. Brief the reviewer and the breaker

The reviewer and the breaker are the newest model, in `orchestrator_capabilities`, of the family the user named (`sol`, `opus`, …), at the effort they named; set no other model option. A provider alone (`gpt`, `claude`) names no family. If the family or effort is missing, ask for it and do nothing else until they answer.

Pin the base: the one the caller passes, otherwise `git merge-base HEAD <remote>/<default-branch>`, where the remote is the one the change merges into (`upstream` on a fork), or `HEAD` when the change is uncommitted only. Run the checks that cover the change, through the repo's verify skill when it has one (`.agents/skills/verify/`), and fix any that fail before round 1. Record the revision they ran on, uncommitted changes included.

Start every round as a fresh `delegate_task`. Pushback and later rounds go in the new brief, never in a follow-up message to a finished reviewer. A timeout or error is not approval: restart the agent that failed, once.

When the diff changes only comments, docs or formatting, run no loop and say so in the final message. In round 1, start the reviewer and the breaker in parallel, the breaker with `isolation: "worktree"`. Skip the breaker when the diff changes no code that runs. In a light run (the tier `see-it-through` passes), start no breaker in round 1; once the reviewer replies, start one scoped to the conditions on its Not verified line that a test could settle, if any.

Both briefs open with this header:

```
Repo: <abs path>  Base: <sha>  Out of scope: <scope>
Standards: <the repo's rule files, such as AGENTS.md or CONTRIBUTING.md; or none>
Setup: <what every shell must run first, such as a pinned-toolchain script, and what a fresh checkout needs, such as an install; or none>
Checks: <results>  Running now: <checks still in progress; or none>
Request: <the user's request or brief, word for word, or its absolute path>
Approach: <the approved approach, or its absolute path; or none>. Its claims are the author's: check the ones the diff relies on.
Acceptance: <the commit or patch holding the acceptance checks written before the change; or none>
Diff: git diff <base>; also read untracked files from git status --short.
Conditions: before reading the diff, write acceptance conditions from the Request: what the user should see or get back on success, failure, cancellation and retry; after a partial failure (what is left in memory, on disk and on screen); on a repeat, or an earlier attempt finishing after a newer one; when an await returns after the user moved on; on every surface that shows the outcome, cached data included; and a way out of every state the change can leave. Write one only where the changed code reaches that case: on the intended path, through every other caller of the changed code, and through every other writer of state the change now trusts (search for both).
```

Reviewer brief, after the header:

```
Review only: read and trace. Do not edit, commit, push, comment, start subagents, or write or run tests or builds.
Write the acceptance conditions as Conditions says, then how you would make the change within the Approach. Start your final reply with both, word for word; the VERDICT line follows them.
Find problems with the change, tracing each condition through the code to what the user sees or gets back. Your approach is a finding only where it meets a condition the diff fails, or meets every condition with less code.
For each bug you find, name its class and look for the same mistake in the rest of the diff and its callers, including a sibling case the change handles differently; report one finding per class, listing every location.
Check the change against the Standards files; tag those findings [standards], and skip what linters and type checks enforce.
Flag as nits code or guards no condition needs, new code the repo or platform already provides, and code that departs from the Standards or the surrounding code's conventions; not style you merely prefer.
Check whether the change introduces competing ownership of state, a decision made in two places, an obligation callers must remember, or a boundary callers can bypass; tag those [structure], naming the code and its consequence, and grade them by the definitions below. A different design with no such consequence is a nit; a larger redesign is a finding only with why the smallest correction can't fix it.
An edit to a check in Acceptance that stops it proving what it promised is a should.
blocker = the intended case is wrong. should = a problem this change causes that a supported action or input can reach: a user action, files on disk, an I/O failure, files the user made, shown by running it or traced through the code, including through callers the diff didn't touch. A test the change adds that can pass without the behaviour it proves is a should.
nit = style, small perf, polish. pre-existing = the same failure happens on the base, shown by a test or a trace, and the change neither makes it easier to reach nor contradicts a claim it makes.
VERDICT: APPROVE or CHANGES, then one line per finding:
S1 [blocker|should|nit|pre-existing] <file>:<line> <claim>. Fix: <smallest fix>
then Checked: one line per condition: <file>:<line> and what that line establishes.
then Not verified: what you could not confirm, and why; or none.
```

Breaker brief, after the header:

```
Break this change. Do not commit, push, comment, or start subagents.
Work only in your own checkout, the working directory you started in, which is a copy of <repo>'s HEAD. First bring over the uncommitted part of the change: git -C <repo> diff HEAD | git apply, then copy the untracked files listed by git -C <repo> status --short. Never change files in <repo> or the user's config, and run nothing that pushes, posts, or notifies; package-manager caches are fine. Skip E2E runs and anything listed in Running now; compile only what your tests need.
Write the acceptance conditions as Conditions says. For each, write and run the smallest test that would fail if the condition broke, asserting on what the user sees or gets back.
For each test below E2E that the change adds as proof, undo the guard it should catch, or break its precondition, run it, then restore the code.
COULDN'T TEST is only for a condition this level can't reach, such as one that needs E2E. A slow queue or your own broken setup is not one: batch your tests into one job, wait for it without cancelling, and fix your setup.
Before you reply, write a patch of your passing tests that cover a condition no existing test covers to <keep path>, and delete everything else you added.
Reply, one line per condition: B1 HELD <condition> — <command>; B2 BROKE <condition> — <command> and the failing output; or B3 COULDN'T TEST <condition> — why. Then one line per proof test: P1 FAILS <test> with <guard> undone; or P2 STILL PASSES <test> with <guard> undone. Then: Kept: <keep path> and the condition each test covers; or none.
```

Pick `<keep path>`: an absolute path outside both checkouts.

## 2. Answer findings

Grade each finding yourself by the reviewer brief's definitions, whatever label it came with. Treat each BROKE and STILL PASSES line as a finding.

- Agree: reproduce it first, with a test that fails on the current code when a meaningful one is practical, otherwise a direct reproduction (command and output) with its limits noted; check a claim about facts, such as what CI runs or what the base does, against its source. Then search the changed code's sibling cases and callers for more of the finding's class, and apply the smallest fix to every instance the change introduced or exposed; list unrelated pre-existing ones as follow-ups. Show the test passes (for a STILL PASSES finding, that the fixed test fails with the guard undone), and keep the test. Prefer deleting or narrowing code over a new lock, cache, helper, or option.
- Disagree: say why, with evidence (a test or command output). A reason read from the code alone, such as "that can't happen", leaves the finding disputed, not dropped or graded down.
- Nit: on code the diff adds, changes or moves, apply it when its fix deletes code, reuses what the repo or platform provides, or brings code in line with the Standards or the surrounding code, keeping every check passing and without trading clarity for length. Decline in one line a nit that adds a path, case, option or compatibility layer, one whose fix changes what the user sees or gets back, and one that is only taste.
- Pre-existing or out of scope: decline in one line.

Commit each test in the breaker's patch, or name the existing test that covers its condition.

Never agree just to end the loop. Re-run the checks and `git diff --shortstat <base>`; remove what the review added outside tests that no accepted finding needs, keeping the smallest correct fix even when it grows the code.

## 3. Next round

Start one only when a blocker or should is open, or behaviour code changed. Send the header with its Conditions line replaced by the round 1 reviewer's conditions, the reviewer brief without its conditions-and-sketch line, every earlier id marked fixed, disputed (with the evidence), or declined (with the reason), and the hunks changed since the last round. Tell the reviewer to review only the open ids and those hunks, write new conditions for the behaviour those hunks change and their callers, mark each earlier id resolved or still open, and number new findings after the last id. When a fix changed behaviour, ordering or ownership, such as moving a write past an await, also start a breaker with the same header, told to write and test conditions only for those hunks and their callers.

## 4. Finish

Done when no blocker or should is open and the last change outside tests, comments and formatting has been through a round; APPROVE ends the loop early on the code it reviewed. Send a fresh breaker on any COULDN'T TEST whose cause can be fixed; list one that needs E2E for the author. If a blocker or should is still disputed after round 3, run the dispute round in [dispute-round.md](dispute-round.md); a finding it leaves INCONCLUSIVE ends the loop finished with unresolved disputes, not approved. Declined nits and pre-existing findings stay declined.

Final message: rounds run, the models, what the findings changed, each tagged behaviour, test, claim, or polish, diff size before and after, any finding dropped because a test or output showed it wrong, and each declined nit or pre-existing finding with its reason. Add what the breaker tested, what broke, which of those the reviewer also found, and each condition no committed test covers. If a dispute round ran, give each outcome. List each unconfirmed risk in plain words. If `evals/results.jsonl` exists and the reviewer model differs from the last one in it, say so and offer a run of the regression suite ([evals/README.md](evals/README.md)).
