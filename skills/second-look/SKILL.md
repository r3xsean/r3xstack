---
name: second-look
description: Use when the user asks to get a second look at something, or another skill asks for a second look.
---

Have a fresh model read work that already exists and say how it would make it better, then settle each point it raises. The work is what the user or the calling skill points at: a proposal, a plan, a back-and-forth's record, a diff.

The second look's model is the newest model, in `orchestrator_capabilities`, of the family the user or the calling skill names, at the effort they name; when they name neither, it is the one the `see-it-through` skill's **Defaults** paragraph gives the second look. If they name only one of the two, ask for the other and do nothing else until they answer. When the model is unavailable, say so in the report and go on without a second look.

## 1. Ask

Start a fresh agent on that model with the request in the user's words, the work, and whatever evidence there is with how to run it, under this brief:

```
<In a sentence, how the work came about: what was asked, and whether one model wrote it or models argued it out.> The request, the work and the evidence are below. You're a fresh pair of eyes and nothing in the work binds you: look wherever you like, run whatever is there to run, and tell us how you'd make this better. That can be a change to it, a different way to do it, or a different reading of the request. If it's already what you'd do, say so. Say what each point rests on. Change no file but scratch files of your own.
<Anything the calling skill adds.>
```

Done when it has replied.

## 2. Settle

What it raises goes back, word for word, to whoever produced the work:

- **A back-and-forth produced it:** into the same back-and-forth, for up to 3 more exchanges and a new record.
- **Otherwise:** you answer each point yourself, adopting it or saying why not, after checking any premise that would change your answer.

Unless every point was adopted as it was given, send the new record, or your answers, to the same agent once more, to concede or to hold with what would change its mind; it raises nothing new.

Done when each point is adopted, conceded or held, or it raised none.

## 3. Report

Say what the second look raised and how each point ended: adopted, conceded or held, a held point with what each side showed and your recommendation. A calling skill says where the report goes. Otherwise it is your reply to the user, with the work as it now stands, and you act on nothing a held point touches until they answer.
