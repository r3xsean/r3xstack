# Automation prompt craft — what only durable prompts have

Disclosed reference for [`writing-steering-files`](SKILL.md), read in full on the **automation-prompt branches** after Scope. The principles shared by every steering file live in `SKILL.md`; this file covers only what a prompt has and a skill or AGENTS.md doesn't.

A **durable prompt** is one dispatched into a session its author won't be in: a scheduled agent, a `/loop`, a subagent dispatch, a headless run, a prompt file checked in and re-run. Prompts typed into a live conversation are out of scope — the human is right there, and these rules exist because they are not.

## The thinnest layer

A prompt is the last and smallest layer over what the run already loads: the harness, the AGENTS.md in scope, any skill it invokes. Anything that holds across invocations belongs in one of those, named from the prompt by its leading word; only this invocation's payload stays — target, trigger, inputs, contract. A long prompt is almost always an unwritten skill.

## Proceed under assumption

On a decision the prompt doesn't resolve, the agent picks a direction and continues. It never halts to ask, and there is no severity clause. Ground the choice in something the run can observe — the state of the target, a convention already present in it, a prior run's output — and name the assumptions taken in the result, so a wrong one becomes a written default on the next edit.

## Idempotency

A durable prompt runs again, against a moved world, with the last run's effects already in it. Name the observable that says this work is done — a marker, a matching key, a timestamp — and what happens when it fires: skip, update, or extend. The test binds the run's effects, not its work; re-deciding is cheap, re-acting isn't.

## No dangling references

"The file I just changed", "yesterday's failures", "the current branch" — each resolves at the keyboard and to nothing on the day it runs. Resolve them while writing, or write the lookup that resolves them at run time.

## Protected paths

Name what the run may write directly, and what it may only propose. The split follows the automation's purpose, and the author sets it: one meant to land changes writes them; one meant to surface findings proposes. Where the work implies a change outside what the run may write, write a proposal to an owned path instead. What fails is leaving the split undeclared — discovering the boundary costs more than declaring it.

## The return contract

Say what comes back, where it lands, and what a failure returns. An automation that returns nothing on failure is indistinguishable from one that never fired.

## The cold-dispatch test

The cold run (`SKILL.md`, step 5) meets the prompt as the run will — verbatim, plus whatever loads in that context, nothing else — with a dry-run note appended: do every read it calls for, make no writes, pushes, comments, or messages. The subagent reports only: what it would have written, and where; references it couldn't resolve to something concrete now; decisions the prompt left open, and what it picked; and how a second run would know the work was already done.
