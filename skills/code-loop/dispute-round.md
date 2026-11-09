# Dispute round

Run once, after round 3, when a blocker or should is still disputed. Start a fresh `delegate_task` with the reviewer's model and effort and `isolation: "worktree"`, carrying the header from SKILL.md §1, the breaker brief's "Work only in your own checkout" paragraph word for word, and:

```
Settle these disputed findings by reproducing them, not by argument.
<each disputed id: the claim, the reviewer's evidence, the author's evidence>
For each, write and run the smallest test or script that shows whether the claimed problem happens, asserting on what the user sees or gets back.
Reply, one line per id: REPRODUCED <id> — <command> and output; REFUTED <id> — <command> and output; or INCONCLUSIVE <id> — what stopped you.
```

Then, for each id:

- REPRODUCED: fix it as SKILL.md §2 says for an agreed finding, keeping the test.
- REFUTED: drop it.
- INCONCLUSIVE: leave the fix out; the finding stays open at its severity, and the final message lists it as an unresolved dispute: the claim, what each side showed, and what stopped the reproduction.

Never ask the user to decide a dispute.
