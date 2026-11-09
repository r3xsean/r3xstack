# r3xstack

My personal agent skills.

Most of them pair your agent with a second model. They argue out a question, take a code change from request to wherever it should land, review and try to break a code change, turn something you found (a post, a video, an article) into a decision about your workflow, decide which model and effort each role in your workflow runs on, and run UI design work with a council of models. The rest support that work: building the checks that prove a change works, writing skills, AGENTS.md files and prompts, and transcribing YouTube videos. Where direction, taste or shipping is at stake, the skills stop for your decision.

**Requires [T3 Code](https://github.com/pingdotgg/t3code).** Several skills hand work to models from other providers through T3 Code's delegation tools, so they don't run in plain Claude Code or Codex. `back-and-forth`, `code-loop`, `see-it-through`, `incorporate` and `model-audit` start the other model that way, and `design-process` starts its council members that way. `incorporate` also reads X links in a T3 Code browser tab.

## The skills

| Skill | What it does for you | How to start it |
|---|---|---|
| [`see-it-through`](skills/see-it-through/) | Takes a code change from your request to its destination (a tested local change, a pushed branch, an open PR, merged or deployed), with another model reviewing. Normally you approve the approach before it builds and the result before it ships. | "see it through with `<family>` at `<effort>`" plus the change |
| [`code-loop`](skills/code-loop/) | Has another model review a code change and try to break it with tests, over up to three rounds (plus one reproduction round for a finding still disputed after them), and fixes or disputes what they find. | "code loop with `<family>` at `<effort>`"; other skills also start it |
| [`back-and-forth`](skills/back-and-forth/) | Answers a question by having your agent and another model each answer it without seeing the other's answer, then argue it out and check the facts the answer rests on. | "go back and forth with `<family>` at `<effort>`" plus the question |
| [`make-verifiable`](skills/make-verifiable/) | Builds, extends or repairs a repo's verify skill: the check commands and scripted flows that prove a change works, with evidence. | "make this repo verifiable"; other skills also start it |
| [`design-process`](skills/design-process/) | Runs UI design work where you set direction and taste: blind design directions, refinement driven by your reactions, and a scored council of models comparing your screens with competitor apps. | ask to design, redesign or polish a UI, to run a design council on screenshots, or to record your reactions to a design |
| [`incorporate`](skills/incorporate/) | Turns a post, video or article you found into a decision about your skills and rules: change them, or record why not. | "incorporate this into my workflow with `<family>` at `<effort>`" plus the source |
| [`model-audit`](skills/model-audit/) | Decides which model and effort each role in your workflow, or in one automation, should run on, from what your plans actually charge and what the evidence shows, and changes only what those roles touch. | "audit the models with `<family>` at `<effort>`", naming the workflow or the model that launched; `incorporate` also starts it |
| [`writing-steering-files`](skills/writing-steering-files/) | Writes or edits a skill, an AGENTS.md/CLAUDE.md, an automation prompt or a product system prompt with you, agreeing the intent and structure before any text exists. | ask to write or change one of those files |
| [`transcribe-youtube`](skills/transcribe-youtube/) | Turns a YouTube video into a timestamped transcript file. | give it a YouTube URL and ask for the transcript |

### Naming the other model

`back-and-forth`, `code-loop`, `see-it-through`, `incorporate` and `model-audit` each need a model family, such as `sol` or `opus`, and a reasoning effort. They use the newest model of that family that T3 Code offers. A provider alone, such as `gpt` or `claude`, isn't a family. If you leave out the family or the effort, the skill asks and does nothing else until you answer.

In `see-it-through`, the same model and effort run every code loop and review, and normally sit on the other side of the debate over the approach. Your agent doesn't argue that debate itself: a runner does, a separate agent that argues your side through `back-and-forth`. Unless you name others, the runner is a Fable agent at medium debating your model; for a key decision (one of the design triggers in [design.md](skills/see-it-through/design.md) fires, and there's a question whose answer could change the approach), it's a Fable agent at high debating Astra at high. When the runner's model or its partner's isn't available, it says so and argues the approach itself with your model. Outside `see-it-through`, `back-and-forth` uses a runner only when you or the calling skill names one.

`design-process` asks only for the models a run needs. When a run will reach the council, it asks at the start who sits on it, with each member's model and effort, unless you already named them. When the capture harness needs new code, it asks which model reviews that code. Its explore designers run on a model you name, or on your agent's.

`make-verifiable` and `transcribe-youtube` don't use another model, and `writing-steering-files` doesn't ask for one: its probes run on fresh subagents.

## How they fit together

- **`see-it-through`** is the end-to-end flow. In a full run it settles the approach with **`back-and-forth`**; in a light run it does so only when its design triggers fire or the strong approaches differ materially; for a change that's already built, it runs none. Before the explainer, it goes through the acceptance conditions in `code-loop`'s brief and names the test that will cover each one that applies, or the limitation it accepts. It reviews the finished diff with **`code-loop`**, and once you've approved the ship message, a fix for a review comment that changes behaviour gets its own code loop. When the repo has no verify skill, or the skill doesn't cover the flow it needs, building that coverage with **`make-verifiable`** becomes part of the approach. When a user can see or do what changed and the verify flow can't capture it, it extends the flow with `make-verifiable`, and when the change alters a flow the verify skill covers, it updates that flow in the same change.
- **`code-loop`** runs the repo's checks through its verify skill when the repo has one. In round 1 of a light run from `see-it-through`, it starts the test-writing breaker only after the reviewer replies, and only for what the reviewer couldn't verify that a test could settle. In any run, a later round starts a breaker when a fix changed behaviour, ordering or ownership.
- **`make-verifiable`** builds the verify skill that `see-it-through` and `code-loop` lean on. Its recording helpers are built to make clips that meet `see-it-through`'s capture rules.
- **`incorporate`** reads videos through **`transcribe-youtube`** and argues what to change with **`back-and-forth`**. When there's a change, it hands the drafting to **`writing-steering-files`**. Adopted scripts are checked with `code-loop`, and repo verification goes through `make-verifiable`. When the source announces a model you could run, it hands the whole run to **`model-audit`** instead.
- **`model-audit`** argues the recipe you picked with `back-and-forth`, reruns `code-loop`'s regression suite when the reviewer or breaker changes model, and makes each change by its file's route: steering files through `writing-steering-files`, launch code and configuration through `see-it-through`, scripts through `code-loop`.
- **`design-process`** puts new harness code through one `code-loop` round before designers use it. During refine, it reviews a structural change with `code-loop` when the change touches code beyond styling and you've named a model.
- **`writing-steering-files`** runs a skill's regression suite, such as `code-loop`'s, before and after an edit to that skill, when the edit touches what the suite exists to test and you've approved the run. Any observed failure the edit answers is added as a case first.

## What they read and write

So you know what lands where before you install:

- `see-it-through` logs lessons, when a run has one, in the changed repo's `.agents/lessons/log.md`.
- `see-it-through` saves acceptance checks that won't be committed, and the runner's record of the debate, outside the repo; `code-loop` saves the breaker's kept tests as a patch outside the repo too.
- `code-loop`'s regression suite builds its checkouts in a temporary folder unless you give it another, and appends each run's results to `evals/results.jsonl` inside the installed skill; your cases go in `evals/cases/` there.
- `make-verifiable` puts the verify skill in the repo's `.agents/skills/verify/`, with its helpers in that folder's `scripts/`, and adds `.claude/skills` as a symlink to `../.agents/skills` when the repo has no `.claude/skills`. Its evidence goes to a git-ignored path.
- `design-process` keeps its files in `docs/design/`, and copies the captures of screens you approve to `docs/design/references/`. Other captures and its findings ledgers go in the git-ignored folder its `harness.md` names, and council packs go outside the repo. When a run builds prototypes, they live in their own entry or route that the production build never includes, with a check that enforces it.
- `incorporate` treats `~/.agents/skills` and `~/.agents/AGENTS.md` as your workflow, and logs each run in `~/.agents/sources/log.md`, except a run it hands to `model-audit`, whose log entry stands for it.
- `model-audit` logs an audit of your own workflow in `~/.agents/models/log.md`, and an audit of an automation where that automation's repo keeps its decisions, with nothing personal in it. Its two scripts only read: `inventory.py` reads the workflow's folder and this machine's Claude Code and Codex session records (`~/.claude/projects`, `~/.codex/sessions`), and `meter.py` reads those records and T3 Code's provider logs (`~/.t3/userdata/logs/provider`). Raw records stay out of the log and out of the skill's folder.
- `writing-steering-files` keeps copies of the files it edits outside their folder while a run lasts, to diff each round against, and deletes them when the run ends.
- `transcribe-youtube` writes each transcript to a temporary file unless you name an output path. When it has to fall back to local speech recognition and faster-whisper isn't already installed, it sets one up in its own environment under `~/.cache/transcribe-youtube/`.

For a repo you don't own, the lessons log and the verify skill go in the folder that holds your process for that repo, never in the upstream repo's files. Where a repo has its own rules, the skills defer to them: `see-it-through` follows the rules of the repo it changes and any process file you point it to, `code-loop`'s reviewer checks the change against the repo's rule files (such as AGENTS.md or CONTRIBUTING.md), `make-verifiable` puts the verify skill where the repo's AGENTS.md says when it names another place, and `design-process` follows the project's AGENTS.md on dependencies, dev servers and what gets committed, asks you before doing anything those rules forbid, and uses another place for its files when that AGENTS.md names one.

## In more detail

### see-it-through

Normally you make two decisions, the approach and the result, and the agent handles the rest. A change that's already built starts at the result, and anything that changes what you approved comes back to you.

1. **The approach.** It first works out where the change should end up, asking only when that's unclear and the answer changes the work. For a bug, it first reproduces it on the base: a failing test and, when a user can see the bug, a capture of the running product. If it can't, it tells you before building a fix, and failure paths it couldn't reproduce become follow-ups rather than new guards. For a feature, it writes down what you should see or be able to do. It then grounds the design in the code, following [design.md](skills/see-it-through/design.md): who owns the behaviour, every caller, whether reshaping something would beat adding to it. It also checks the destination for newer commits and open work on the same behaviour. A design question it could answer by running something is settled with a throwaway experiment rather than by asking you. When even the smallest approach costs more than the problem, it recommends a smaller version or no change, and you decide. It sends you an explainer: the problem, why it happens, what changes, the approach, the alternatives weighed and what a reviewer may ask. It builds nothing until you approve. Any reply other than an approval goes word for word into the same back-and-forth (in a light run with no back-and-forth, back to the agent) and comes back as a revised explainer.
2. **The result.** Before changing behaviour, it keeps the reproduction and every acceptance check it can write in advance as a baseline that runs again on the final candidate. Once built, it shows the reproduction passing, simplifies the diff, runs a code loop on it and, when a user can see or do what changed, captures it (for a bug, before and after through the same flow). Simplifying, as [simplify.md](skills/see-it-through/simplify.md) sets out, looks only at code the diff adds, changes, moves or leaves unused, never changes what the user sees, and uses the repo's own simplification skill when it has one. Then it sends a ship message: a recap, what changed since the explainer, the evidence, the captures, the write-up, the diff and the exact action it will take. When the code loop ended with unresolved disputes, the message leads with them. Before sending it, it checks the destination again for work overlapping the change. Saying "see it through" approves no push, PR or deploy; only your approval of the ship message does.

Along the way:

- **Full or light.** A run is full when the changed behaviour reaches persistence, concurrency, authorization, migrations, a public contract, destructive effects or shared state ownership, or when the agent can't yet tell how the changed code is reached or how well tests cover it. Otherwise it's light, and a light run that turns up one of those becomes full.
- **The explainer stays true.** If a test, demo or review changes what you get, it sends a revised explainer and stops again. Smaller discoveries, such as using a different internal helper, go in the ship message instead.
- **Captures are made for a quick look.** Following [capture.md](skills/see-it-through/capture.md): when the result is a state, a paired before/after screenshot, with the recording of how a user gets there under it when an action leads to that state; a recording alone when the interaction itself is the result; the same data and framing before and after, setup kept off camera, and waits time-lapsed under a visible label. The agent looks at each capture before offering it, and a capture of the base or of a failed run never stands as a pass. A change with nothing to see gets no capture.
- **Public text is checked.** Before a PR description, reply or status update goes out, a fresh reviewer on the other model checks every claim against the evidence, the captures and the diff. A claim the evidence doesn't back is cut. Before every push, it reruns the checks and redoes the captures that the changes since could affect.
- **After approval,** it carries the change to its destination. It builds on other people's pushes instead of overwriting them. Every review comment gets a fix or a one-line reason, and a fix that changes behaviour gets its own code loop. A request that changes the scope or the approach goes back to the explainer; one that applies beyond this change comes to you with its link. When a fact proves posted text wrong, it corrects the text. When the change lands, closes or is replaced by someone else's version, it compares what reached the destination with what it last verified and reports what differs, without re-adding what others removed on purpose. For a deploy, it runs the verify flow against what's deployed.
- **Lessons.** When a problem gets past the code loop, or the loop finds a blocker or should, it logs the lesson in the repo's `.agents/lessons/log.md` (for a repo you don't own, in the folder that holds your process for it). Then it reads the log and lists follow-ups in its final message: for a lesson seen twice, a lint, type, test or verify check when a check could catch it, or a line in the repo's AGENTS.md when it needs judgement; for two lessons in one module, or two of one bug class, a structural question, naming the cause they share before any refactor is proposed. A refactor runs as its own see-it-through.
- **Changes already made.** If you say the change is already built, it skips the explainer and the back-and-forth. It pins the base, finds the checks that fail on the base and pass on the change, writing one only for a promised behaviour none of them proves, and the ship message becomes your first approval.

### code-loop

The agent pins the base and runs the checks that cover the change, fixing any that fail. Then it starts fresh agents on the other model:

- a **reviewer** that only reads and traces. It writes acceptance conditions before reading the diff, then grades each finding as blocker, should, nit or pre-existing.
- a **breaker** in its own worktree. It writes the smallest test for each condition and checks whether the change's own tests still pass with the guard they should catch undone. Tests that cover something no existing test does are kept as a patch, and the agent commits each one or names the existing test that covers its condition.

When the diff changes only comments, docs or formatting, there's no loop. When it changes no code that runs, there's no breaker. Otherwise both start together in round 1, except in a light run, where the breaker starts only after the reviewer replies, and only if a test could settle something the reviewer couldn't verify.

The agent grades every finding itself by the reviewer's definitions, whatever label it came with, and treats each condition the breaker broke, and each of the change's tests that still passes with its guard undone, as a finding. For an agreed finding, it reproduces it, preferably with a failing test, and applies the smallest fix to every instance of the same mistake that the change introduced or exposed, preferring to delete or narrow code over adding a lock, cache, helper or option. For a disputed one, it pushes back with evidence. "That can't happen", read from the code alone, leaves a finding disputed rather than dropped. It never agrees just to end the loop. A nit on code the diff adds, changes or moves is applied when its fix deletes code, reuses what the repo or platform already provides, or matches the repo's standards or the code around it; otherwise it's declined in one line.

A further round runs only while a blocker or should is open or behaviour code changed, and an approval from the reviewer ends the loop early. If a blocker or should is still disputed after round 3, a fresh agent tries to reproduce it ([dispute-round.md](skills/code-loop/dispute-round.md)). A reproduced finding is fixed and a refuted one dropped. An inconclusive one leaves the loop finished with an unresolved dispute rather than approved. You're never asked to settle a dispute.

The final message reports the rounds run, the models, what the findings changed, the diff size before and after, each declined nit or pre-existing finding with its reason, what the breaker broke, and each risk still unconfirmed.

[`evals/`](skills/code-loop/evals/README.md) holds a runner that replays `code-loop`'s current briefs against past changes where it missed a bug. It's for judging an edit to the briefs, or to how findings are answered, before the edit lands, or for rechecking when the reviewer model changes; once the suite has results, `code-loop`'s final message offers a run when the reviewer model differs from the last one recorded. Its README's commands run the copy installed in `~/.agents/skills/`. This repo ships no cases; you add your own as that README describes.

### back-and-forth

Your agent writes its own answer first, so its view is fixed before it reads the other model's. The other model gets your question and context but nothing of that answer. They then exchange critiques in the same thread. Agreement doesn't count as evidence: every premise that would change the conclusion is checked against a source, a command or the code, even one both sides accept.

It stops when the positions match, each side has given its reasons and every checkable premise is checked, or after 3 exchanges past the opening unless you named another number. Your agent owns the conclusion. Its record gives the reasons, the alternatives that lost and why, what changed either side's mind, the other model's strongest remaining objection (with the agent's call when the two still disagree), each premise marked checked or unchecked, and a link to the other model's thread. If the other model fails twice in a row, it concludes with what it has and says the other model dropped out.

When you or a calling skill names a runner, a model and effort to argue your agent's side, your agent doesn't debate at all: it starts the runner with your question word for word, and the runner's record is the result. Whatever you add later goes to the same runner. Where your agent has evidence against a claim in the record, it sends that back as a further exchange rather than overruling the record itself.

### make-verifiable

It builds a **verify skill** in the repo. That skill is the one place agents learn which commands check a change, how to launch the right build, how to drive a flow and judge its outcome, where the evidence goes and what wasn't verified, and how to clean up. In a repo you own it lives at `.agents/skills/verify/`. In a repo you don't own, it goes in the folder that holds your process for that repo, never in the upstream repo's files.

- It works in three modes: set up, extend, or repair. It covers only the flows you name.
- Every check CI runs maps to a local command or is marked CI-only. It adds an ordering check, which runs the real code through every order of replies and events up to a bound, only when the request or a lesson names state that several operations change across awaits. A failing order counts as a bug only once a plain test on the real code reproduces it.
- Its helpers pass the repo's lint and format and stay out of the repo's own test run, so adding them doesn't change what the repo's checks run.
- Flow helpers launch the product as close to how users reach it as the environment allows. They drive it with throwaway data, assert what the user sees and what was saved, and save evidence, including a screenshot or recording when the outcome is visible. They clean up only what the run created.
- A missing prerequisite or unsupported flow reports INCOMPLETE, never a pass. Each new assertion is seen to fail on a broken outcome before it's trusted.
- When a verify step fails, it decides whether the cause is the environment, drift in the verify skill, or a product regression. It fixes only the drift and reports a regression as a bug.
- Recording helpers follow [recording.md](skills/make-verifiable/recording.md): the raw recording is kept, the clip is trimmed to its start and end marks, and waits are time-lapsed by default. Each clip comes with a pacing report, a contact sheet and key frames for reviewing it.
- It commits only when you, or the skill that called it, say so.

### design-process

You decide direction and taste. Models judge execution: whether the task can be done, whether the numbers are true, whether anything breaks, hides or misleads. A score or a council never chooses between directions or overrules a decision you recorded. If the project has its own design skill, that skill comes first.

It keeps its files in `docs/design/` unless the project's AGENTS.md names another place. They are a product brief, a `DESIGN.md` of your decisions and reactions, a `harness.md` describing how screens are run and captured, and a `run.md` per run. Templates are in [`templates/`](skills/design-process/templates/).

- **New UI:** bootstrap → explore → you pick → refine → council → you approve a reference → holdout → ship.
- **Existing UI:** bootstrap → council → approve → ship, with refine first when you want visible changes. A narrow tweak starts at refine.

A run enters at the phase you ask for, but bootstraps first whenever the product brief, `DESIGN.md` or `harness.md` is missing. The phases:

- **Bootstrap** reads the project first, then asks you, in one message, for what's still missing. It builds a capture harness on fixture data from the real product.
- **Explore** has three designers each build a different direction, blind to the current UI and to each other. They're shown to you under random letters, and you pick, or ask for another round.
- **Refine** responds to your reactions. It makes a local change directly, shows 3–6 variants on the real screen when you're unsure, and makes a structural change within your decisions and the craft floor, reviewing it with `code-loop` when it changes code beyond styling and you've named a model.
- **Council** runs scored rounds on fresh screenshots, compared with one or two competitor apps. It suggests members from different providers and never substitutes one that's unavailable. The default target is every member scoring every screen at least 9 and above every competitor, unless you set another. It acts on a finding when more than one member raised it, or when one member raised it at high or medium severity and the agent confirmed it in the captures. Execution problems get fixed. Findings that contradict your decisions are skipped. Changes with a real tradeoff are held for you. It reports after each batch of five rounds, or sooner if the target is met, and runs another batch only on your yes. When the work ends in a pull request, the score table goes in its description.
- **Holdout** comes after your first approved reference. A fresh agent designs a surface not yet designed from the skill, the project's files and the harness alone, and lists every guess it had to make. Each guess is fixed in the file that should have answered it, or recorded as open.

Only your words approve a reference screen; scores never stand in. Every reaction you give goes into `DESIGN.md` in your exact words. Its scope is never widened, and it becomes a general decision only when you state it generally or say yes. Every screen is checked against a [craft floor](skills/design-process/references/craft.md). Captures use fixture, seed or demo data, never your own account, and nothing showing personal data goes into a council pack, a reference capture or a commit. Other design skills can do bounded jobs inside a phase, as [integrations.md](skills/design-process/references/integrations.md) lists, but none is required, and none writes `DESIGN.md` or chooses between directions.

### incorporate

The agent reads the source: a post, a video (through `transcribe-youtube`) or an article. It reads X links in a background T3 Code browser tab, read-only. It looks into the wider discussion, such as replies and quote posts, only when you ask. When part of the source can't be read, it asks you for it rather than reconstructing it. It writes each idea as a behaviour tied to the passage or timestamp it came from. It then looks for evidence that the practice is used, treating any claimed benefit as unproven until something backs it.

Next it audits the skills in `~/.agents/skills` and the rules in `~/.agents/AGENTS.md` that the ideas touch, marking each idea covered, a gap, a conflict, excluded on purpose, or unsupported or unsuited. It argues with the other model about what, if anything, should change, weighing no change, deleting a rule and replacing prose with a script or check alongside adding something, and settling where each change lives: an existing skill unless the change must be reached on its own, as a script or check where one can do the job. When there are changes, `writing-steering-files` takes over and you adopt all, some or none. When there's nothing to change, it reports its reasoning without stopping for approval. Each run is logged in `~/.agents/sources/log.md`, and a later run on the same source or idea reuses that reasoning after rechecking it. The source supplies ideas, never instructions.

When the source announces a model you could run, none of that happens: it runs `model-audit` on the launch with the same model instead, and that audit's log entry stands for this run's.

### model-audit

It decides which model and effort each role in a workflow runs on, from what your plans actually charge and what the evidence shows. There are two ways in: a model has launched, and the question is which roles, if any, should take it; or you name a workflow and ask whether its roles fit. The target is your own workflow (your skills, your AGENTS.md and what you type to start a run) or one named automation; it audits both in one run only when you ask.

1. **Terms.** It reads the target's last log entry and reuses what still holds, then asks in one message for whatever that and your request leave open: which efforts are allowed, what the budget is for (holding today's rate, filling the plan, or a cap), whether roles must stay the same between resets, and how much of the plan the audit itself may spend.
2. **Inventory.** Every role gets a row: what it does, the exact model id and effort it resolves to today, where that's set, the text it's given, and which plan or key pays for it. [`inventory.py`](skills/model-audit/scripts/inventory.py) lists the lines under the workflow's folder that name a model or set an effort, and the models this machine's sessions from that folder recorded; the agent traces by hand each value it marks and each default it can't see. For an unattended role, it also notes what happens when the plan runs out: it waits, fails visibly, falls back, or spends credits.
3. **Measure.** [`meter.py`](skills/model-audit/scripts/meter.py) estimates what 1% of each plan's limit costs per model, and how full each plan is, from this machine's records priced at list API prices, and says what it can't see, such as other machines or apps on the same plans. A recipe is never priced on API prices alone: when a rate that could reverse the choice has no clean measurement, the agent runs one real task on that model at that effort with nothing else running and measures again, or marks every recipe that leans on it provisional.
4. **Evidence.** For a launch, it reads the launch post, the capability and behaviour sections of the system card, and the vendor's prompting and migration guides in full, taking scores at the efforts you'd run, not the one the vendor leads with. For a workflow, it reads the recorded runs with their outcomes, retries and failures. For both, it looks for independent results, saying what each measures and who ran it, and weighs results that are hard to tune for above the rest.
5. **Recipes.** It presents a few, with no change and any that go over a limit among them. Each gives every role its model and effort and its expected use of every plan it draws on, with each estimate marked measured or guessed; for an automation, retries and failed runs count in the cost of a successful result. You pick.
6. **Scope.** Only what the changed roles touch is in scope: their text, the handoffs into and out of them, and instructions they share, checked against the roles that didn't change. A launch is no reason to clean up anything else. A line goes only when it covered a weakness of the model that left the role, repeats another line, describes mechanics that no longer exist, or conflicts with something it can show.
7. **Test.** It runs the smallest tests that could change the choice: a role's regression suite when it has one, and for an automation, recorded inputs replayed on the candidate with publishing and writes off, compared on outcome and cost per successful result.
8. **Debate.** It goes back and forth with the other model on the picked recipe and the changes it needs.
9. **Change.** Each change goes through the route its file has: a steering file through `writing-steering-files`, launch code and configuration through `see-it-through` in that repo, a script through `code-loop`. What an unattended role does when the plan runs out is set in its configuration, never in its prompt. When it audits your own workflow, automations that pin an affected model are listed as follow-ups, not changed.
10. **Log.** It appends a dated entry with the target, each role's model, effort and exact id, where each is set, the measured rates and how they were measured, why the recipe won and what lost, what's approved but not yet made, and what's still unmeasured.

The scripts need Python 3.

### writing-steering-files

It covers eight branches: create or edit a skill, an AGENTS.md, an automation prompt (one that runs unattended) or a product prompt (the system prompt behind a feature other people use). Every branch runs the same loop; an edit grills and shapes only the change, not the whole file:

1. **Scope:** the file and the behaviour change. For an edit, "currently the agent does X; after this it should do Y."
2. **Grill:** every rule becomes "given X, the agent does Y" and is tested for ambiguity, no-op, overreach and whether it belongs elsewhere.
3. **Shape:** the structure, one line per section, before any text is written.
4. **Draft.**
5. **Probe:** only the runs you approved, and none when you approved none. These can be probes against the real feature for a product prompt; a skill's regression suite, when the skill has one and the edit touches what it tests; a replay of the failure an edit answers, when the original prompt and context are still available; or, for a skill, an AGENTS.md or an automation prompt, a cold run by a fresh agent that reports where it had to guess.
6. **Walkthrough:** what each section encodes, every judgement call, then the real text, as a whole-file diff the first time and only what changed in later rounds, each headed with its size before and after and a flag when the edit only adds.

You approve the scope, the intents and the shape before any text exists, in one message when none of them waits on your answer to another, then the real wording. Edits leave approved behaviour alone; when the change conflicts with something already in the file, it shows you the conflict and proposes replacing or removing the old rule. Each kind of file has its own craft file, such as [skill-craft.md](skills/writing-steering-files/skill-craft.md), which the agent reads before the grill.

### transcribe-youtube

It runs a bundled Python script on the URL, which writes the transcript to a file and prints its path for the agent to read. It tries the video's captions first and, when there's no suitable track, transcribes the audio locally with faster-whisper, using an existing install or setting one up in its own environment. No API key is needed. The file's header records the language and whether captions or local speech recognition produced it. You can ask for a preferred language, an output path, or text without timestamps. It needs Python 3 (`py -3` on Windows) and `yt-dlp` (`python -m pip install -U yt-dlp`).

## Install

```bash
git clone https://github.com/r3xsean/r3xstack.git
mkdir -p ~/.agents/skills ~/.claude/skills
cp -R r3xstack/skills/* ~/.agents/skills/   # Codex
cp -R r3xstack/skills/* ~/.claude/skills/   # Claude Code
```

On Windows (PowerShell):

```powershell
git clone https://github.com/r3xsean/r3xstack.git
New-Item -ItemType Directory -Force "$HOME\.agents\skills", "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force r3xstack\skills\* "$HOME\.agents\skills\"
Copy-Item -Recurse -Force r3xstack\skills\* "$HOME\.claude\skills\"
```

To update, `git -C r3xstack pull` and copy again. Copying never deletes: when a skill is removed or renamed here, delete its old folder from your skills folders yourself.

## How this repo works

It's published automatically from my private skills source: a job checks every five minutes and, when the skills have changed, publishes them as one commit. Changes go into the private source first, so open an issue rather than a pull request.

## License

[MIT](LICENSE)

<!-- r3xstack-readme: ce73a9707f1de1ee0513a25b24de173c9a97bfcd9a7195252715a04992b9d19c -->
