# Harness contract

What a project's harness must provide, on any stack. Build a capability only when the run needs it, and record what exists, with its commands, in `harness.md`.

## Basic (every run)

- **Fixture data from the real product.** Export it from the real engine, API or database, or use the project's seed data; never values made up for the design. Cover a normal case, empty, single item, the longest names and values, a failure state, and every state the brief names. Exports are deterministic: the same input gives the same files.
- **Isolation from production**, from the first prototype, when the run builds prototypes. Prototypes live in their own entry or route that the production build never includes. While exploring blind, they import none of the app's components or styles. A script or lint enforces both, in the check the project runs before merging.
- **Capture command.** It screenshots every case at every size in `harness.md` (web default: 1440×900, and 390×844 at 2×; a desktop app uses its minimum and typical window), in every role and theme the brief says matters, both the first viewport and the full page, with:
  - a fresh browser context per case, a fixed clock, reduced motion, and a fixed locale and time zone;
  - waiting for the screen's ready signal (or its main content, when it has none), fonts and every image before the shot;
  - a manifest: git sha and dirty flag, fixture stamp, viewport and scale, and per case PASSED or FAILED with its error and files.

  A failed case keeps no image and is never replaced with an older one. The command also writes one contact sheet per viewport, and its output goes to a new folder per run in the gitignored captures folder.

## Interactive (explore rounds with working screens, and every council)

- A scenario switch (URL parameter or equivalent) selects which fixture set renders.
- A written contract of stable test hooks for each task's controls and results, plus a ready signal on each screen. It covers behaviour only, never appearance.
- The capture runs each task's flow step by step, asserts the results against the fixtures, records clicks and taps per step, and fails a case on any console error.

## Comparative (when the user wants options)

- A variant switch on the real screen (`?<element>=1..N`), so variants render in context with real data.
- A comparison sheet: every variant of one element side by side, at every viewport, in one image.
- A gallery route showing one component across many samples, built only when the user asks for one.

## Competitor captures (when the council runs)

Capture the equivalent screens of the competitor apps named in `harness.md`, at the same viewports, signed in with a demo or test account. Capture them once per council batch and name each file after the pattern it is compared for. If an app can't be captured (login wall, native-only), ask the user for screenshots. Never let the council score against an app it has no capture of.

## Reviewing harness code

New harness code gets one code-loop round, with the model the user named in bootstrap, before designers use it. Fix or report each material finding. A further round needs a named reason.

## Worked example

One working shape: a dev-only entry the production build excludes; fixtures exported from the app's real engine; a test-id contract; a Playwright capture script that writes a manifest and contact sheets; and an import-boundary check that runs in the build. When the project already has a harness like this, read its README and contract to see what it covers before adding to it.
