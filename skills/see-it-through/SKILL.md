---
name: see-it-through
description: Use when the user says "see it through with" a model.
---

Take a code change from the user's request to where it should end up, with another model as reviewer. The user decides twice: the approach, at the explainer, and the result, at the ship message. Everything between is yours.

The other model is the newest model, in `orchestrator_capabilities`, of the family the user named, at the effort they named. The same model and effort run every back-and-forth, code loop and review below. If the family or effort is missing, ask for it and do nothing else until they answer.

## 1. Destination and rules

Work out where the change ends: a tested local change, a pushed branch, an open PR, merged, or deployed. Ask only when it's unclear and the answer changes the work. Saying "see it through" approves no push, PR or deploy; the ship message's approval does.

The rules of the repo you're changing, and any process file the user points you to, win where they differ from this skill.

**A change already built.** When the user says the change is already made, what's built is the approach, and the ship message is the first approval: send no explainer and run no back-and-forth. In place of steps 2 and 3:

- Pin the base: for an unmerged branch, its merge-base with the branch it merges into, taken after its last merge of that branch; once merged, the commit before the change. Ask when it isn't clear. When the change is already merged, the destination is where this run's follow-up commits go; ask when that isn't clear.
- Write the request from the user's words and what the change says of itself (commit messages, PR text), marking what you inferred.
- Find the checks that fail on a worktree of the base and pass on the change, starting with the tests the change already has (run them on the base with only the change's test and harness hunks applied), and write one only for a promised behaviour none of them proves; for a change with no failure to show, such as a speed-up or a refactor, a check of what it promises. Set the tier as step 2 does. Keep as the acceptance baseline, as step 4 keeps it, the fewest of those checks that prove each behaviour the change promises, noting which were written after the change; the change's other tests stay open to simplify.md.
- Write the approach as built in a file: what changed, design.md's grounding and its structural question answered of what's built, and step 3's failure check.

Then continue at step 4 from showing the reproduction passing, and give the code loop that base and that file as its Approach. The ship message says no explainer was approved, and carries any structural alternative and any finding that changes what the user gets.

## 2. Reproduce

For a bug, reproduce it on the base before writing a fix: a test that fails, and, when a user can see the bug, the running product showing it, captured as [capture.md](capture.md) says, by hand when the verify flow can't capture yet. For a feature, write what the user should see or be able to do. When you can't reproduce a bug, tell the user before building a fix, and write anything you say about it as "from reading the code (not tried)". A check that finds nothing counts only once you've seen it find the thing when it is there.

Build no guard for a failure path you haven't reproduced; list it in the explainer as a follow-up instead.

Reproduce and prove through the repo's verify skill: `.agents/skills/verify/` in the repo, or where the repo's AGENTS.md puts it. When there is none, or it doesn't cover the flow you need, reproduce by hand for now and make building that coverage with the `make-verifiable` skill part of the approach.

Then set the tier. **Full** when the changed behaviour reaches persistence, concurrency, authorization, migrations, a public contract, destructive effects or shared state ownership, or when you can't yet tell how the changed code is reached or how well tests cover it; judge by the callers and state writers you find, not by file names. **Light** otherwise. A light run that turns up one of these becomes full.

## 3. Design and the explainer

Read [design.md](design.md) and do what it asks before choosing an approach. In a full run, go back and forth with the model on the approach (the `back-and-forth` skill), with design.md's proportion estimates in its Context as premises to check and a smaller version and no change among the options; in a light run, do so only when design.md's triggers fire or the strong approaches differ materially, and otherwise write the approach yourself. When a design question is a fact you could observe by running something, settle it with a throwaway experiment in an isolated checkout or scratch data, not by asking the user; the experiment ships nothing.

Then write the failure check: go through the Conditions in the `code-loop` skill's brief header, plus who relied on the behaviour you're changing, and for each that applies, name the test that will cover it or the limitation you accept.

Send the user the **explainer**, in plain language, under these headings, in order. Say each thing once.

- **The problem:** what a user sees today, who hits it and how often (observed or estimated; no reports means unknown, not rare), why it matters, and your reproduction, with its capture when it has one; for a feature, what's missing today. When the user asked for the change, open with their words.
- **Why it happens:** the cause, in plain terms; for a feature, what stands in the way today. Leave this heading out for a feature when nothing does.
- **What changes:** what the user will see or be able to check when it's done, and what's out of scope. Where something that would change the work is missing, ask for it here.
- **The approach:** what changes in the code and where, how you'll prove it, including any `make-verifiable` work and which checks ship with the change or stay as evidence, what it costs to ship and keep and why that's worth the reach and harm under The problem, and the failure-check entries a reviewer would care about.
- **Alternatives weighed:** every strong alternative, design.md's structural option among them whenever a credible one exists, each with why it lost.
- **What a reviewer may ask:** each likely question, with its answer.

Then stop: build nothing until the user approves. A plain approval in any wording lets you build. Anything else goes word for word to the model as a further exchange of the same back-and-forth, past its exchange limit, and comes back as a revised explainer; stop again. In a light run with no back-and-forth, revise the explainer yourself and stop again.

The approval covers the explainer as written. When a test, a demo or a review changes what the user gets, its visible behaviour, compatibility, scope, the action you'll take to ship it, or a tradeoff the explainer accepted, quote the sentence it falsifies, work it out with the model, send a revised explainer that says what changed, and stop again. Smaller discoveries, such as using a different internal helper, go in the ship message's "what changed since".

## 4. Build and prove

Before changing behaviour, keep the reproduction and every acceptance check that can run before the change exists: commit the ones the explainer ships, and save the rest, or all of them when nothing will be committed, as a patch outside the repo. Together they are the acceptance baseline, and all of it runs again on the final candidate: any later edit to it goes to the code loop and the ship message with its diff and whether it changes the promised behaviour.

Build the approved approach, in the order design.md sets. When the change alters a flow the verify skill covers, update that flow in the same change. Show the reproduction from step 2 passing, through the verify skill and in the running product when the user can see it. Then simplify the diff as [simplify.md](simplify.md) says. Then run a code loop with the model on the full diff (the `code-loop` skill), giving it the user's request, or the brief that stands for it, as the Request, the explainer as the Approach, the acceptance baseline as the Acceptance, and the tier.

On the final candidate, when a user can see or do what changed, capture it through the verify flow, extending the flow with `make-verifiable` when it can't, and for a bug capture the same scenario on the base through the same flow, so the before and after match. Choose, make and review the capture as [capture.md](capture.md) says, and check it shows what you'll say it shows. A capture shows the change and the checks prove it, so a capture of the base or of a failed run never stands as a pass. A change with nothing to see gets no capture.

## 5. Write-up

Draft the PR, issue or release text from the project's templates, with the captures where the template has room for them, or under a heading of their own. On GitHub, attach them when you publish with `gh pr create --attach` (or `gh pr edit`) unless the repo has its own tool; when it exits non-zero, look for the PR before retrying, since it may already exist. Before any public text that states a fact goes out (a description, a reply, a status update), a fresh reviewer of the model checks it against the evidence, the captures (a recording as its frames and pacing report) and the diff: every claim true and backed, every ticked box true. Cut a claim the evidence doesn't back; don't hedge it.

Before every push, rerun the check behind each ticked box and each claim, and redo each capture, that the change since could affect.

## 6. Ship message

Send the user: a two- or three-sentence recap of the explainer, what changed since, the evidence, the captures, the write-up, the diff, and the exact action you'll take on approval. When the code loop finished with unresolved disputes, lead with them: each claim, what each side showed, and what approving ships with it. Before sending it, redo design.md's overlap check. Stop until they approve it.

## 7. Through to the destination

Take the approved action, then carry the change to its destination:

- Before each push and before acting on a notification, fetch the remote head and check the change's current status. Build on others' pushes, comparing trees rather than commit hashes; don't replace their work with a stale local version. When the change lands, closes or is replaced by someone else's version, compare what reached the destination with your last verified head and open findings. Report what differs or didn't make it, without re-adding what they removed on purpose.
- Every review finding, inline or in a review's body, read in full, gets a fix or a one-line reason; one that also happens on the base is judged as `code-loop` judges a pre-existing finding. A fix that changes behaviour gets a code loop.
- When a fact proves posted text wrong, correct the text.
- A request that changes the scope or the approach goes back to step 3 and, once built, to a new ship message; one that applies beyond this change goes to the user when it arrives, with its link: doing it here doesn't do it elsewhere.
- For a deploy, run the verify flow against what's deployed.

## 8. Lessons

When the user, a PR reviewer or anything after shipping caught a problem the code loop missed, or the code loop found a blocker or should, add an entry to `.agents/lessons/log.md` in the repo you changed; for a repo the user doesn't own, in the folder that holds their process for it. Each entry: the date, the change, what was caught and by whom, the module, the bug class, and the cause.

Then read the log. A lesson a check could catch, seen twice, becomes a lint, type, test or verify check; one that needs judgement, seen twice, becomes a line in the repo's AGENTS.md; two entries in one module, or two of one bug class in any modules (such as state another operation changes during an await), become a structural question, naming the cause they share before any refactor is proposed. List each as a follow-up in your final message; a refactor runs as its own see-it-through.

Done when the change is at its destination, or when you've reported the exact blocker and what's left, and the lessons entry, if one is due, is written.
