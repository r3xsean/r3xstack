# What a test is worth

Read when deciding whether to write, ship, keep, rewrite or delete a test, in the repo's suite or in a verify flow. Reading it starts no verify setup or suite audit by itself.

- **Valid while the behaviour holds.** Assert what users or callers see or get back and what's saved, so a change that keeps the behaviour keeps the test passing. Pin exact text, markup, snapshots, source text or call order only where that exact detail is the contract. A fixture or harness that has to move doesn't make a test a change detector.
- **Removals.** A test whose only job is to show something was removed is evidence for that change, not a test to ship. Ship one only when it guards a requirement that still holds against a plausible regression, such as where the old URL now goes, old data still being read, a request or side effect that must never happen, or a security rule; it then asserts that requirement, not the absence.
- **One rule, one check.** A rule copied across per-component tests, such as a retired word appearing nowhere, goes in one check over every surface it covers, where one can.
- **Rewrite or delete.** A test that breaks these, or stays green with its behaviour broken, is rewritten to assert the contract when it's that contract's only coverage, and deleted otherwise, with any helper or fixture it leaves unused.
- **Doubt.** When an existing test's value is in doubt, show it: break the behaviour and see it stay green, or make an edit that keeps the behaviour and see it fail.
