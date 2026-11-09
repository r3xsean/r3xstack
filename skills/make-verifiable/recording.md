# Recording helpers

Read when a flow's helper records video. The clip it makes has to meet see-it-through's capture.md; this is how the helper gets there. Keep the implementation as small as the flow allows, but not the editing rule: every recording declares its actions, holds, results and real-time scopes, is trimmed to verified start and end marks, and has the time outside those spans compressed by default. A recording with nothing to compress needs only an identity time map. Add nested-span handling, the change-detection guard and overlays beyond the labels capture.md requires only when a recording needs them.

- **Raw first.** Keep the raw recording unedited and make the clip from it by an explicit time map. Never pace a clip with sleeps in the flow.
- **Spans.** The helpers that drive the flow log spans with an id, a kind, and a start and an end (the end logged in `finally`), with a format version:
  - *action* (pointer movement, typing, a click and its immediate response): real time;
  - *hold* (reading time the flow's author asked for): shown at its requested length, frozen or trimmed in the edit, whatever the run took;
  - *result*: a protected hold, plus a highlight and a caption;
  - *real time* (a timing claim): never compressed;
  - everything else, including the helpers' own settling pauses: compressed by default, so the author never has to mark a wait.
  When spans nest, resolve them into one non-overlapping map; when the format changes, render an old log by its own version.
- **Bounded compression.** At most ~8×. A wait still long at that rate becomes a cut with a card, and a warning.
- **Change detection guards, never decides.** Per-pixel change over a contrast threshold, on a capture without the pointer, may only slow the edit (play a change inside a compressed span at 1× with a little lead-in and run-out) and is reported; it never speeds anything up. Check it on real encoded clips before making it the default.
- **Overlays** (captions, before/after labels, time-lapse labels and cut cards, highlights, and any painted pointer or click marks) go through the same time map.
- **Ends.** Open at a "settled" mark (the scene's own element present plus a couple of rendered frames), logging both the requested and the settled time, and end at the end mark, after the final hold. Judge the opening by the encoded first frame: DOM readiness and an unchanging image don't show the intended scene was captured. A recording with no end mark is a diagnostic, not a clip.
- **Review output.** Write beside each clip: a pacing report (length, time compressed, holds over ~3 s, boundary problems, and, when change detection runs, the longest real-speed stretches with no change and any change inside a compressed span); a uniform contact sheet; and frames just before and after each click, result and compression boundary, plus the first and last frame. Name any diagnostic that isn't available: without a detector, a compressed span is not known to be free of changes.
