# Bootstrap

Gets a project ready for design work: the product brief, DESIGN.md, `harness.md` and a `run.md` exist, and the user has confirmed the facts that would change a design decision.

1. **Read before asking.** Product docs, any existing `PRODUCT.md` or `DESIGN.md`, the README, routes, screens, real copy, and analytics if the project has them. Label each fact **confirmed** (the user or an authoritative doc says so), **inferred** (from code or behaviour) or **unknown**. A design doc from another tool (impeccable's `DESIGN.md`, a style guide) describes the current look: treat it as evidence, not decisions, unless the user says otherwise, and never overwrite it.
2. **Ask once.** One message holding only what is still missing:
   - the inferred facts that would change a design decision, for the user to confirm;
   - the unknowns that matter;
   - the keep question: "Is there anything you already know must stay or change: a pattern from the current product, a look (light or dark, dense or airy), an interaction? Skip it if you don't know yet.";
   - the sizes and states every screen is judged in: viewports or window sizes, plus roles and themes when the product has them;
   - which one or two apps doing the same job the council should compare against;
   - council members (SKILL.md), when the run will reach the council and they aren't named;
   - the model for the code-loop review, when the harness needs new code.

   Ask a second round only when an answer opens a new gap that would change a design decision.
3. **Write the files** from `templates/`, filling every slot from what you read and heard. Leave a slot you could not fill marked `unknown`; never invent a product fact.
   - Each answer to the keep question becomes a reaction-log row in DESIGN.md (type `like` or `dislike`, design "current UI", the user's words). A look or interaction constraint the user set for this run goes under Fixed in `run.md`. Only a rule the user stated generally goes into Decisions.
   - Never record a convention of the current product as a user preference unless the user said it.
4. **Harness.** Read [harness-contract.md](harness-contract.md) and build the capabilities this run needs, reusing what the project already has (preview routes, fixtures, Playwright, Storybook).

Done when the four files exist with every gap marked `unknown`, and the harness captures the run's surfaces at every size `harness.md` names.
