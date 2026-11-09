# Council brief template

Copy this into the pack as `brief.md`. Fill the `{…}` slots and change nothing else, so rounds stay comparable.

---

# Design review: {product}, {surface list}

You are a senior product designer reviewing {product}: {one line on what it is and who uses it}. This is a read-only review. Use only the files in this folder: don't open browsers, run anything, read source code or look at other files.

- `product-brief.md` says what each surface must let people do and how its numbers must be read.
- `craft.md` is the quality floor every design must meet, whatever its style.
- `decisions.md` records choices the product owner has made; where it disagrees with the other two, it wins. Don't report a design for following a decision. Report a decision only if the captures show it blocking a task, and say so.

Read them all, then every image, before writing anything. Judge whether the design works and meets the floor, not whether it matches your taste.

## The pack

{Viewport sizes and scale.} Captures are the first viewport unless marked full-page. Flow steps are in order, with the clicks or taps taken so far. Our captures use fixed demo data.

Ours: {file — surface — scenario — viewport — first viewport | full-page | flow step N, one line each}

Competitors: {file — app — the pattern it is here to compare — viewport, one line each}

Missing captures: {list, or "none"}

Out of scope (deliberately not built; don't report): {from run.md, or "none"}

## What to do

1. **Problems.** List every real problem, each with:
   - an id (P1, P2, …) and the files;
   - what is wrong, quoting on-screen text where it helps;
   - why it matters to the user;
   - severity: `high` (blocks or misleads a task), `medium` (slows or confuses) or `low` (polish);
   - confidence: high, medium or low;
   - the craft.md rule, when one applies.

   You may add a suggested fix, labelled as a suggestion. Report only what the captures show. Put what you can't see (behaviour, performance, contrast you can't measure) in a "Cannot verify" list.
2. **What works.** What is good and must stay, with the file.
3. **Scores.** Score each surface 1–10 at each viewport, and score each competitor's equivalent screen on the same scale. 10 is the best tool of this kind you know.

## Reply format

Prose and short lists, ending with exactly one fenced `json` block:

```json
{
  "problems": [
    {"id": "P1", "files": ["x.png"], "summary": "one line", "severity": "high", "confidence": "high", "craft_rule": "Nothing over the work", "suggestion": "optional"}
  ],
  "cannot_verify": ["one line each"],
  "scores": {
    "ours": {"<surface>": {"desktop": 0, "phone": 0}},
    "competitors": {"<app>": {"<surface>": {"desktop": 0, "phone": 0}}}
  }
}
```
