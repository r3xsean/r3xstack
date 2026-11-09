# Making a capture

A capture is for a reviewer who gives it a few seconds. Plan it backwards from the result, the one moment they must see.

- **Medium.** When nothing moves (a badge, a label, a count), a paired before/after screenshot of that region, cropped with enough context to recognise the control, at native resolution, taken once the result has rendered. A recording only when the interaction or the transition is the point. Offer what explains the change, not everything you made.
- **Matched.** Before and after use the same fixtures, framing and script, with only the code under test different, and neutral labels ("Before · <base>", "After · this change"). Prefer one sequential Before → After video with a title card per half to two players; side by side only when the UI is large enough to stay legible at half width.
- **Setup off camera.** Whatever both versions show identically is setup: start just before the action where they diverge.
- **Short.** Aim for about 15 s per clip for a single interaction. Over ~20 s needs a reason; a second scene often works better as its own clip.
- **Paced for the viewer.** Actions at real speed; a reading hold on each result, ~1.5–2 s for a simple state and longer for text; everything else time-lapsed under a visible label ("⏩ 13 s"), or, when it would still be long, cut with a "13 s later" card. A timing claim ("updates within 5 s") plays in real time.
- **Says where to look.** A one-line caption per scene, naming events the viewer can't see ("sync finished"), and a box or a modest zoom on the result while it's held.
- **Legible where it's embedded.** Players shrink video to the page column; crop or zoom to the region that matters during the hold.
- **Clean ends.** The first frame is the poster: the real starting scene. The last is the result, never teardown.

In a message to the user, embed each capture by its absolute path. Before offering a capture, look at it: a screenshot as the image itself; a recording through what its tooling makes from the finished file (`make-verifiable`): the contact sheet, the frames around each action, result and boundary, and the pacing report. Re-edit or recapture when the result is unreadable, a boundary is wrong, or an unintended wait plays at real speed; reading holds and real-time scopes stay as they are.
