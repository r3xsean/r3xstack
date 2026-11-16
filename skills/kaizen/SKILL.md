---
name: kaizen
description: Use when the user says "kaizen".
---

Find what's worth improving in a codebase, judge every finding, and when the user says "go", see each one through from this thread as its orchestrator. Nothing in this skill edits the code: every change is a `see-it-through` run.

## Settings

The user can change any of these by saying so, in their own words, when they start ("kaizen the sync code, just performance, chat only"); the rest keep their defaults. Each named model is the newest of its family in `orchestrator_capabilities`.

| Setting | Default | What the user can say |
|---|---|---|
| Scope | The whole repo | An area or path; "since the last pass"; "this branch", where the pass reads the branch's head and the files it changed, and step 7's runs start from that branch and land on it |
| Focus | Every lens in [lenses.md](lenses.md) | Lenses by name or in their own words; "also look for X" adds one |
| Depth | One reviewer per lens family per slice, plus one per whole-repo lens | "Quick": one reviewer per slice with every lens, and no whole-repo reviewers. "Deep": one reviewer per lens per slice |
| Direction | The direction reviewer runs, and its suggestions have no cap | "No direction"; "direction only", where it is the only reviewer |
| Stages | Probes and debates | "Skip probes"; "no debates", and you give the verdicts yourself |
| Report | An HTML page, plus a short list in chat | "Chat only" |
| Models | Reviewers and the runs launched at step 7: the model and effort this thread runs on. Probes: Sol at high. Debates: the runner and the other model from the `see-it-through` skill's Defaults. Close calls: its second look | Any role, with model and effort |

Start agents all at once wherever a step says so. When the harness refuses more, start the rest as earlier ones finish.

## The record

The record for a repo is `~/.agents/kaizen/<owner>-<repo>/`, which syncs privately with the rest of `~/.agents` and is never published. When the user keeps a process folder for the repo, the record goes there instead, and that folder's own rules for taking on and launching work win over steps 4 to 7.

- `items/<slug>.md`: one file per finding, kept across passes, in the format of [briefs.md](briefs.md) "Item file".
- `STATUS.md`: the board (each launched item, its thread, its stage and what it waits on) and the run log (each pass's date, revision, scope, the settings that differed from the defaults, and the exact model id of every role).
- `runs/<date>-<revision>/`: this machine's working files for a pass, kept out of sync: `reports/` for the reviewers' reports, `baselines/`, `debates/` for the debates' records, and `scratch/`.
- `report.html` and `index.md` (one line per item: slug, verdict, status, theme, goal): built by `python scripts/report.py <record folder>` from this skill's folder; never edited by hand.

## 1. What's known

Fetch the default branch of the repo the work lands in: upstream's, for a fork. Its head is the pass's revision. Make a detached worktree of it in the temp folder: the pass's tree, which every reviewer, probe and debate reads. Remove it when step 5 is done.

From the tree, read the repo's AGENTS.md or CLAUDE.md, README, CONTRIBUTING, CI config, verify skill and lessons log. Read the indexes of its decision docs (ADRs, `PRODUCT.md`, `DESIGN.md`, `CONTEXT.md` and the like) and the docs themselves for what the scope touches; reviewers get their paths. In a repo the user doesn't own, also read upstream's rules for contributions (CONTRIBUTING, `SECURITY.md`, any AI policy, issue and PR templates): they decide what counts as a finding there and how each one lands. Read the record's `index.md` and its last pass. Find the hotspots in scope from `git log`, counting code, not data or content files.

Measure the baselines the repo can produce in the tree without touching anything shared, such as build and test times, bundle sizes and CI durations from run history, and keep the raw output in `baselines/`. Then cut the scope into slices: parts a reviewer can read all of closely, about 10,000 lines of code each, drawn along the code's own boundaries and weighted by hotspots. Leave out generated and vendored code, and say so. Tell the user in one line how many slices and reviewers that makes, and carry on without waiting.

Done when every slice is named with its paths, every baseline is measured or marked with why not, and the record has been read.

## 2. Audit

Start every reviewer at once, each a fresh agent on the reviewers' model with [briefs.md](briefs.md) "Reviewer" filled in: one per lens family per slice, and one per whole-repo lens, as [lenses.md](lenses.md) groups them. Focus, Depth and Direction narrow the set.

Done when every reviewer has written its report, or has failed to twice. List each failed reviewer's slice and lens, and the code left out of slices, under `## Not covered` in `reports/lead.md`.

## 3. Merge

Read only each reviewer's closing lines, one per finding. Group the findings into themes, findings that share a cause or a fix: a theme's items are each other's siblings for batching. Findings two reviewers both made go in the same theme. Then start a fresh agent per theme, all at once, with [briefs.md](briefs.md) "Merge" filled in. It reads the write-ups, checks them against the code, and writes the item files.

Done when every finding is an item, part of one, or dropped with its reason.

## 4. Size

Give every item still open a reach probe, all at once: a `delegate_task` on the probe model with [briefs.md](briefs.md) "Probe" filled in. A probe sizes an item; it doesn't re-audit the code or judge the item.

Done when every open item has its probe in its file, or is marked unprobed with why.

## 5. Judge

Give each theme a worth-it debate, all at once: a `delegate_task` on the runner with [briefs.md](briefs.md) "Debate" filled in. Every item comes back as do, batch, drop or wait.

A debate is a **close call** when the runner and the other model end on different verdicts, when an unchecked premise would flip the verdict, or when the runner calls it near even. When a close call turns on one number nobody measured, have that number measured (a probe of that number only) and debate that item again, as a new debate given the number. Get a second look at the record of any other close call (the `second-look` skill) and settle it as that skill says. Put its report under the item's Debate section, and set the Verdict line to the verdict it settles on.

Every verdict stands without asking the user, close calls included. This replaces the second look's wait for the user on a point it holds: that point goes in the report with each side's case, and the verdict stands.

Done when every item has its verdict.

## 6. Report

Build the report, and show it to the user with `html_preview` and `html_render`. Then send in chat:

- how many items there are per verdict;
- each item to do or batch, one line each;
- the close calls;
- what wasn't covered;
- how to answer: "go", "go except <items>", "go on <items>", or "<item>: grill me", which launches that one without auto approve, so its grill and explainer come to the user.

Done when the report is shown. Then stop until the user says go.

## 7. Go

From "go" on, this thread is the pass's orchestrator. Read no code yourself from here: probes, debates and runs do that, so this thread's context lasts across every run.

- **Launch** each item to do, and each batch as one, as its own thread with [briefs.md](briefs.md) "Launch" filled in. Use `t3_thread_launch` in the repo's project, in a new worktree from the remote default branch, on the runs' model, with full access. In a repo the user owns, the destination is merged into the default branch, through a PR where the repo merges through PRs. Items that cite the same files launch one after another, each once the one before has landed; the rest launch at once. A direction item launches without auto approve, so its product decisions come to the user. Record each thread in `STATUS.md` and in its item.
- **No verify skill.** When the repo has none, first launch one run of the `make-verifiable` skill, set up for the flows the launched items touch, and launch the rest once it has landed.
- **A repo the user doesn't own.** Follow upstream's rules from step 1. An item lands as a PR from the user's fork, unless upstream asks for an issue first or the item needs the maintainer's product call. In that case, draft the issue yourself and add it to the ship list below. Once the user approves, file it, and the item waits on the maintainer's reply. A security item goes the way upstream's `SECURITY.md` asks, never as a public issue or PR unless that file allows it.
- **Ship.** Runs send a short form of their ship messages here. When the user approves here ("ship all", "ship <items>"), pass their exact words to each run they cover with `t3_thread_send`. They may also approve in a run's own thread.
- **Messages from runs.** "<slug> shipped", "dropped" or "blocked": update the item and `STATUS.md`, rebuild the report, and launch whatever waited on it. "<slug> lead": a new item; probe it and judge it as above, in a fresh tree of the default branch, and launch it on do.
- **Waiting items.** What an item waits on is an event, such as a merge or a maintainer's reply. Check each with `gh` or the T3 tools whenever a message arrives.

Done when nothing is running and nothing can launch. Then write a closing summary at the top of `STATUS.md` (what shipped, what was dropped, what still waits), rebuild the report, and settle the thread (`t3_thread_organize`).

## Later passes

"Kaizen continue", in any thread, rebuilds the board from `STATUS.md` and the item files and checks each launched thread in `t3_thread_list`. It then sends each run still going this thread's link, as where to report from now on, and carries on at step 7. An item judged before the code it cites changed gets a fresh probe and debate before it launches.

A new pass in a repo with a record starts at step 1 as usual. Its reviewers get the items on record for their slice and say which are gone or changed, and step 3 decides what reopens.
