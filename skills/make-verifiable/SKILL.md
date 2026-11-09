---
name: make-verifiable
description: Use when the user asks to make a repo verifiable, or another skill needs a repo's verify skill created, extended or repaired.
---

Build and maintain a repo's **verify skill**: the one place agents learn how to check and prove a change in that repo. It answers five questions: which commands check this change, how to launch and identify the right build, how to drive a named flow and judge its outcome, where the evidence is and what wasn't verified, and how to clean up what the run created.

## Where it lives

In a repo the user owns: `<repo>/.agents/skills/verify/`. If the repo has no `.claude/skills`, add it as a symlink to `../.agents/skills`; never replace an existing real directory. In a repo the user doesn't own (an upstream they contribute to), put it in the folder that holds their process for that repo, never in the upstream repo's files. The repo's AGENTS.md wins where it says otherwise.

Helpers live in `scripts/` inside the verify skill's folder. They pass the repo's lint and format like any code, and stay out of the repo's own test run, by file name or config, so adding them doesn't change what the repo's checks run. Evidence goes to a git-ignored path.

## Scope

Three modes, picked from the request:

- **Set up:** no verify skill yet. Build the checks and the flows the request names.
- **Extend:** add a flow, or a check the repo gained.
- **Repair:** a verify step failed or drifted.

Cover only the flows named; never catalogue the whole product unasked.

## 1. Find what exists

Read the repo's AGENTS.md, package scripts, task runners, git hooks, CI workflows, E2E frameworks and existing harnesses. Done when every check CI runs maps to a local command or is marked CI-only, and every existing harness you'll reuse is named.

## 2. Checks

List one command per check kind (lint, types, build, tests, and so on), pointing at the commands that already exist. Add a wrapper only when several must run together; it prints what it ran and exits non-zero when any of them fails. Narrow checks to the changed area only by the repo's own selection rules; when what a change can affect is unclear, run the full set.

When the request or a lessons follow-up names state that several operations change across awaits (user actions, replies, events), add an **ordering check**. It drives the real code, replaces only the outside boundary (IPC, network, timers) with a model of the order that boundary can deliver its replies and events in, runs every order up to a stated bound, and asserts the properties after each step. Write the properties from the intended behaviour, not from the code under test, cite each ordering rule in the boundary model to the code or doc it comes from (`file:line` at a named revision), so a change there tells the next agent to recheck the model, and allow every order those sources don't rule out. It reports the bound, the orders run, and whether the search was exhaustive within the bound. A failing order counts as a bug only once a plain test on the real code reproduces it.

Done when each command has run on the current tree to a result, each wrapper has been seen to exit non-zero on a failing input, and each ordering check has been seen to fail on a defect planted in each guard it covers, then pass once restored. A command the environment stops from running is a blocker to report, not a result.

## 3. Flows

For each flow, write executable helpers that:

- start the prerequisites the flow needs, such as a local database, when they can be started locally and safely;
- launch the product as close to how its users reach it as the environment allows, and wait until it is ready, reusing an existing harness where one exists; each gap from the real path, such as a fake transport in place of a live service, goes on the flow's not-verified line;
- record what ran: the revision, uncommitted changes and, when a build runs, the build actually exercised;
- drive the real path with throwaway data;
- assert the visible outcome and the persisted effect;
- save evidence to a path the helper prints;
- when the outcome is something a user sees, save a screenshot or recording of it with the evidence, using the repo's own test tooling where it can capture, otherwise a simulator or browser recording; a helper that records follows [recording.md](recording.md);
- clean up only what the run created.

A missing prerequisite, an unavailable runner or an unsupported flow reports INCOMPLETE with the reason, never a pass. A capture the flow can't make, frames included, reports the capture INCOMPLETE with the reason and leaves the flow's verdict as its checks found it.

Before trusting a new or materially changed assertion, show it fail on the broken outcome (the original bug on the base, a negative fixture, or a fault planted in a throwaway checkout or isolated data), then pass once restored. Never break a shared app or an external service to do it. Routine runs don't repeat this.

Done when every flow in scope has passed once, each new assertion has been seen to fail, and each new capture has been made once and looked at.

## 4. Repair

When a verify step fails, first decide which it is: the environment, the verify step drifting from the product, or a product regression. Fix only drift in the verify skill. A regression is a product bug, reported, not edited away. An expected outcome changes only when the approved intent changed. Rerun a repaired step before trusting its evidence.

## 5. Write the verify skill

`SKILL.md` with the description `Use when checking or proving a change in <repo>.` and a body holding only: the check commands; per flow, its command, what it asserts, its prerequisites, its evidence path and, when it captures, how to ask for the capture and where it goes; and the report contract: PASS, FAIL or INCOMPLETE per check and flow, with what ran and what wasn't verified, and per capturing flow the capture's path, "none required", or INCOMPLETE with the reason. Mechanics live in the helpers, not the prose.

Commit only as the calling skill or the user says. Report what you added or changed, the failures you saw each new assertion and wrapper catch, and what is still INCOMPLETE.
