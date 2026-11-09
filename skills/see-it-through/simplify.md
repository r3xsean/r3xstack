# Simplify

Read at step 4 of [SKILL.md](SKILL.md), once the reproduction passes and before the code loop. When the repo has its own simplification skill, such as `deslop`, run it in place of "Look for"; "Never" and "Done" still apply. "Never" wins over "Look for".

Ask "could this be simpler?" of every hunk of `git diff <base>`, and only of code the diff adds, changes or moves, plus code it leaves unused. Simplifications elsewhere become follow-ups.

## Look for

- Code no acceptance condition needs: options, parameters or flexibility nobody asked for, an abstraction or helper with one use whose name says nothing the inlined code doesn't, a guard on a path whose callers already guarantee it, a cast that silences the type checker.
- New code the repo or platform already provides: an existing helper or component, the standard library, an installed dependency. Never add a dependency for a few lines.
- Logic repeated within the diff, nesting an early return would flatten, a decision made in two places.
- Comments that restate the code. Keep the ones that say why.
- Tests in the diff that catch no regression you can name that another test or layer doesn't already catch. Delete whole tests, then any helper or fixture they leave unused.

## Never

- Change what the user sees or gets back, even where no check covers it; propose that in the ship message instead.
- Cut validation at a trust boundary, error handling that prevents data loss or a double effect, a security check, an accessibility affordance, or anything the Request asks for. Code you moved keeps its error handling and validation.
- Touch a test in the acceptance baseline, or a helper or fixture it uses.
- Trade clarity for length: a shorter version that takes longer to read, such as a nested ternary or a dense one-liner, is not simpler. Follow the repo's conventions, not your preference.

## Done

Rerun the checks; revert a simplification that makes one fail, rather than editing a test. Done when every hunk has been asked, every simplification found is made or kept for a reason under "Never" (its size is no reason), the checks pass, and you've noted for the ship message each test you deleted, by name.
