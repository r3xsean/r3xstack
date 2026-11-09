# Product prompt craft — what only user-facing prompts have

Disclosed reference for [`writing-steering-files`](SKILL.md), read in full on the **product-prompt branches** after Scope. The principles shared by every steering file live in `SKILL.md`; this file covers only what a product prompt has and the others don't.

A **product prompt** is the system prompt behind a feature other people use — a chatbot, an assistant, an agent shipped inside a product. Two facts follow. The reader is a third party, so a wrong output *is* the product, not a bad turn. And this one can be tested before it ships: the feature runs on demand, so authoring ends in a probe loop rather than in live use.

## The starting skeleton

Convergent across production prompts. A default to depart from, not a mandate.

1. **Role and scope** — who it is and what it covers, in a sentence or two.
2. **Capability boundaries** — what the product cannot do. Without this the model invents features that don't exist and promises them to users.
3. **Tool catalog** — one entry per tool, written as *when to use*.
4. **Request-class protocols** — the routing for each kind of question: which tools, in what order, and what the answer leads with.
5. **Empty-tool and failure handling** — what to say when the tools return nothing, and where to send the user instead. The most-skipped section.
6. **Grounding** — every claim traces to a tool result. Name the canonical source per claim type, and forbid filling gaps from model memory.
7. **Output contract** — the format, bound to the channel it renders on.
8. **Refusals and scope limits** — what it declines, and in what words.

## Which surface owns the fix

*Root cause first* (`SKILL.md`), applied to a product: a failure has four possible homes — the prompt, a tool's description, a tool's output, or a missing product capability. A prompt paragraph compensating for a misleading tool output is a workaround, and it leaves the defect live for every other path that reaches it. Markdown arriving in a channel that can't render it is an output-contract bug; an assistant that "reschedules" by booking a second appointment needs a tool, not a warning.

## Tool descriptions are prompt

A tool description is not a docstring — it is prompt text the model reads every turn, and it drives tool selection more than the body does. Write each as *when to use*, disambiguate it against the siblings it will be confused with, and name the canonical tool for a claim type where one exists. Vague descriptions produce invented arguments, not just wrong routing.

## The probe loop

Draft, then test before the walkthrough. The agent runs the loop; the human meets its results in the walkthrough.

- **Derive probes from the intents.** Every intent from the grill becomes at least one question a real user could ask. An intent that resists this was never a behavioural intent — surface it rather than skipping it.
- **Literal or varied.** Use the exact question when phrasing is the variable under test; otherwise write several phrasings of the same situation.
- **Run them against the real feature**, through whatever drives it — its API, its CLI, the browser. When nothing reaches it, run the prompt directly against the model and say so; only when even that is impossible, hand the probes to the human.
- **A fresh subagent judges, not the drafter.** Give it each transcript and the intent it probes; it returns pass or fail with the line that decides it. A drafter grading its own prompt passes what it meant to write, and generic quality scores miss what the intent asks. Transcripts the judge can't call go to the walkthrough.
- **Triage each failure to its surface**, fix there, and re-probe what changed.

Done when every intent has been probed and each one passes or has its failure, with transcript, surfaced in the walkthrough. Once the feature is live, real conversations replace invented probes and the same triage applies.
