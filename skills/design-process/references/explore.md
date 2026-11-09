# Explore

Several designers each build a different direction for the same surfaces, blind to the current UI and to each other. The user compares them and picks. The first section is for the session running the round; the second is the designers' brief.

## Run a round

1. **Name the open question** in `run.md`: what the round has to answer, e.g. "how does the team list answer 'which team should I run?'". Also list what is fixed: the keep list's `like` rows, constraints the user set, and what earlier rounds carried.
2. **Write three stances**, each a different, consequential answer to the open question.
   - On task screens, vary structure: what the eye lands on first, how items are grouped and compared, where the evidence sits, how much imagery leads. One stance may be a wildcard.
   - Vary palette or visual identity only when the open question is the look itself (a marketing page, a brand) and nothing fixed settles it.
   - Assign the stances to random letters and record the key only in `run.md`.
3. **Carry fixed items.** Copy only the named items (tokens, component files, cropped captures) into each slot's `carried/` folder, never another direction's notes. Write `carried/CARRIED.md`: each item, the user's words behind it, which part is fixed and which part a `dislike` opens.
4. **Start one designer per slot** in parallel, each a fresh agent on the model the user named, or on yours. Give each the brief below, its slot, its stance, and the round's look-and-fix budget (default 3). Ask for a variant gallery only when the user asked for one.
5. **Check shared truth while they build.** Verify that the fixtures, the brief and any numbers derived from the product's logic are correct, using assertions and scripts first. Use one reviewer, given the brief, the fixtures and the derivation code, only for what no assertion covers. Fix problems at the source, and tell the designers when a fix changes their data. No design review runs on directions.
6. **Present.** Show only the letters, the running screens and a contact sheet per viewport. Name every unbuilt feature so it isn't read as taste. Stances, designers' notes, scores and findings stay back until the user has reacted.
7. **Record the reactions** (SKILL.md), then ask what carries forward: into another round, or into refining the picked direction.

Done when the user has picked a direction, or has asked for another round and said what carries.

## Designer brief

You are one of several designers, each building a different direction for the same surfaces. The user will compare them side by side and choose. Your job is a direction that is distinct, complete, and passes the craft floor.

**Read**, in order: the product brief; DESIGN.md (follow any recorded decision; where none, the look is yours); the skill's `references/craft.md`; the harness docs and fixture docs named in `harness.md`; your stance; and your slot's `carried/CARRIED.md` when present.

**Blind boundary.** Do not open, search or import:
- the app's own components and stylesheets;
- other slots, except the copies in your own `carried/` folder;
- screenshots or mockups of the current product;
- docs describing the current look (style guides, another tool's DESIGN.md), even when the project's AGENTS.md points UI work at them.

The harness and fixtures are infrastructure you may read. When the brief and the fixtures disagree about data, the fixtures win; note the conflict in your report.

**Carried items:** use them as given and change only the part CARRIED.md opens. Your stance governs everything else. Copy what you use into your own files and leave `carried/` untouched.

1. **Plan before code.** Write `DIRECTION.md` in your slot:
   - one idea sentence, grounded in the product's subject rather than software trends;
   - the signature move: one memorable thing, with everything around it kept quiet;
   - palette as 4–6 named hex roles, type families and their roles, and a type scale;
   - ASCII wireframes of each surface at every viewport;
   - how navigation and global controls work at each width.

   Then check the plan against the defaults AI-made UI clusters around: warm cream with a serif and terracotta; near-black with one acid accent; hairline broadsheet columns; identical rounded cards with one shadow and gradient washes; an eyebrow over every heading and middot meta strings. Where one of your choices matches a default without a reason specific to this product, revise it, and record each revision as one line. Carried items are exempt.
   Done when DIRECTION.md holds every item above and the default check is recorded.
2. **Build every surface** in your slot as working code: every contract hook, every fixture scenario, real assets, every viewport designed together. A feature the brief names but the fixtures don't feed gets a real entry point that does nothing yet, listed as unfinished.
   **Gallery** (only when your task asks for one): render the named component in the number of variants given (default 4), each from the same samples at the width it gets on your screens. Any two variants must differ in at least two of these: what the eye lands on first, how facts are grouped and ordered, where the key numbers sit, how much imagery shows. A recolour or respacing is not a variant. Your screens use one variant.
   Done when the capture command reports every case passing.
3. **Look and fix.** Check the contact sheets, then every first-viewport shot, against every rule in craft.md. Fix what you find and recapture, within the round's budget.
   Done when a full craft pass on the final captures finds nothing you can fix within the budget.
4. **Report.** Append to DIRECTION.md:
   - what is unfinished or weaker than intended, plainly (unfinished work is not read as taste, so hiding it only hurts your direction);
   - any craft rule you broke, and why;
   - facts you found missing;
   - the look-and-fix rounds you used.

   Your final message gives your slot, the idea sentence and the capture manifest path. Don't argue for your direction; you have not seen the others.

**Boundaries:** write only inside your slot (capture output excepted). Add no dependencies; report a need instead. If the harness or fixtures are broken, report it rather than patch them. No commits, pushes or branch changes. Use only real product copy and data; add no invented features, numbers or claims.
