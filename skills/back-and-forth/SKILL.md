---
name: back-and-forth
description: Use when the user says "go back and forth with" another model.
---

Reach the best answer to the user's question by arguing it out with another model. You own the conclusion.

## 1. Openings

The other model is the newest model, in `orchestrator_capabilities`, of the family the user named (`sol`, `opus`, …), at the effort they named; set no other option. A provider alone (`gpt`, `claude`) names no family. If the family or effort is missing, ask for it and do nothing else until they answer.

**A runner.** When the user or the calling skill names a runner, a model and effort to argue your side, don't run the debate yourself. Start the runner as a fresh `delegate_task` on that model and effort, carrying the question word for word, the Context, the other model's family and effort, the path to save its record to when you have one, and the instruction to run this skill and reply with the record of §3; its task says it may start the other model. Send whatever the user adds later to the same runner with `t3_thread_send`. Its record is the debate's result: where your own evidence contradicts a claim in it, send that evidence back as a further exchange; don't overrule it yourself.

Write your own answer in your message first, so it is fixed before you read theirs. Then start the other model with a fresh `delegate_task` carrying this brief, without your recommendation:

```
You're in a back-and-forth with another model to reach the best answer to the question below. You won't see its answer before you give yours.
Question: <the user's question, verbatim>
Context: <facts, absolute file paths, and constraints the user gave>
Give your own answer, its reasoning, and how confident you are. Mark each premise your answer rests on as checked (say how) or unchecked. Later messages bring the other model's answer and critique. End every reply with your current position in one line and, if it changed, the argument or evidence that changed it.
```

## 2. Exchanges

An exchange is one message from you and its reply. Send every exchange as a `t3_thread_send` to the same child, never a new `delegate_task`. Your first message carries your answer and your critique of theirs; later ones carry your updated position and your critique of their last reply. End each message with your current position in one line, plus what changed it if it did.

Agreement is not evidence. Every premise that would change the conclusion if it were false gets checked against a source, a command or the code, whether it was disputed, agreed by both, or given up by one side; either of you can check it, and the result goes in the next message.

Stop when both positions match, each side has given its reasons, and every premise that can be checked has been, or after 3 exchanges past the opening, unless the user named another number. If a reply errors or times out, resend once; if it fails again, conclude with what you have.

## 3. Conclude

The final message is the record:

- the conclusion and its reasons;
- each alternative seriously considered, and why it lost;
- what changed either side's mind;
- the other model's strongest remaining objection, with your call when the positions still differ;
- each premise the conclusion rests on, marked checked (how) or unchecked;
- whatever else the question asked the answer to contain;
- the other model's thread, by its link.

If the other model dropped out, say so. When you are a runner, the record is your whole final reply, and you also save it to the path you were given, if any. Don't end on a question.
