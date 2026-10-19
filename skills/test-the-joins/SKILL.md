---
name: test-the-joins
description: Build tests from how real users actually move through the code, not from how each function looks in isolation. Uses graphify to read the codebase as a graph, maps every way a user (or another system) enters it, and turns each path into journey tests covering the happy path AND the unknown ones — retries, second sessions, restarts mid-step, providers that accept then fail, settings read from a different place than they're written. Use when the suite is green but real bugs keep shipping, before trusting a big test count, when adding tests to an untested area, when auditing or trimming a test suite, or when asked "am I testing the right things?".
---

# test-the-joins

Unit tests check that each part works. Real bugs live **between** the parts: the second call, the retry, the page refresh, the provider that said "OK" and then didn't deliver, the setting written under one key and read under another. A suite can be thousands of tests and 95% covered and still miss all of these, because every test fakes exactly the join where the bug lives.

This skill flips the order. **Read the code first (with graphify) to learn how a real user will use it, then write tests for every path they can take — the happy one and the ones nobody planned for.**

Read [PRINCIPLES.md](../../PRINCIPLES.md) once. Then follow the steps.

## Requirements

- [graphify](https://github.com/Graphify-Labs/graphify) (Apache-2.0): `uv tool install graphifyy` (or `pip install graphifyy`). Build the graph from the code that is actually running (a clean checkout of the deployed commit, not a stale branch):
  ```bash
  graphify update .            # code graph, no LLM needed
  graphify explain "fnName()"  # callers + callees with file:line
  graphify query "how does a booking reach the calendar" --budget 1500
  graphify path "EntryPoint" "SideEffect"
  ```
- The project's own test runner. Nothing else is required.

## The steps

### 1. Map how users enter (the doors)
List every way work enters the system: HTTP routes, webhooks, queue/job handlers, cron/loops, UI pages, CLI commands, inbound messages. For each door, ask graphify where it goes:
```bash
graphify query "entry points routes webhooks job handlers" --budget 2000
graphify path "<door handler>" "<external side effect>"
```
Write them down in `test-plan.md` as a table: door → who uses it (end user / admin / other system / timer) → the side effects it can cause (DB rows, messages, emails, calendar events, CRM records, charges).

### 2. Walk each door like a real user — then like the real world
For each door, trace the path with `graphify explain` on every function it calls until you reach the side effects. At each **join** (a call to another service, a queue, a DB write read later by someone else, a setting, a retry boundary, a cache) list the scenarios. Use the scenario matrix in [references/scenario-map.md](references/scenario-map.md):

- **Happy:** the path the code was written for.
- **Unhappy (known):** the provider is down, rejects, times out; input invalid; permission denied.
- **Unknown (the ones that ship as bugs):** the same thing arrives twice; a second session for the same person; a retry after half the steps already ran; the process dies mid-step; the provider says "accepted" and fails later; a value is written by one layer and read by another under a different shape; two writers fill the same record with different knowledge; a feature flag routes to a different code path; a name or setting is copied somewhere outside your database (a template at a third party, a CRM, a cache).

Every scenario gets one line: *who does what, in what order, and what the person on the far end should receive.*

### 3. Audit what the current tests really check
Run the scanner and read its report next to your scenario list:
```bash
python3 skills/test-the-joins/scripts/audit_tests.py <repo-root>
```
It flags (details: [references/audit-checklist.md](references/audit-checklist.md)):
- fakes of a boundary that **always succeed** (a send stub that always returns an id, a lock/claim stub that always says yes);
- a real step replaced by a constant `"ok"`;
- tests that **pin wording** (exact strings, regex over source files, hashes of prompts) instead of behaviour;
- helpers and routes nothing calls (confirm each with `graphify explain` AND a text search before deleting).

Mark each scenario from step 2: **covered end to end / partly / not at all.** Coverage % is not the answer — the modules that break are often the best covered. The question is whether any test drives the *join*.

### 4. Build fakes that can fail like the real thing
A fake is only useful if it can do what reality does. Replace always-succeeds stubs with stateful fakes from [references/realistic-fakes.md](references/realistic-fakes.md):
- a messaging/payment gateway with modes `ok | accepted_then_failed | rejected_with_200 | down`;
- a lock/idempotency store with `processing | stale | failed | completed`;
- a job runner whose lease can lapse and whose process can **die mid-step** (no cleanup runs);
- a config fixture built from a **real stored row** (keys and types copied from production, values made up), fed through the same reader production uses.

Fake only at the **outermost edge** (the HTTP call to the third party), never in the middle of your own code.

### 5. Write journey tests from real data
Each journey replays a real path end to end through the real code, using recorded payloads (anonymised: names → "Visitor", phone numbers → made-up, keep language and shape). Template: [references/journey-template.md](references/journey-template.md). A journey asserts **what the person on the far end gets** — one confirmation, not two; the owner alerted once, with the booking; a "not confirmed" state when the provider failed later — not which internal function was called.

Good first journeys (they catch the most):
1. A save that happens in two passes (fast save, then a later background save with more information).
2. The same person in a second session / tab / device.
3. A retry after half the steps succeeded.
4. The process dies mid-send, restarts, and must deliver exactly once.
5. The provider accepts, then reports failure.
6. A setting read from a real stored row, through the real reader, to the real consumer.

### 6. Prove every new test by putting the bug back
A test you never saw fail proves nothing. For each journey, revert the fix (or break the behaviour) and confirm the journey fails, then restore:
```bash
skills/test-the-joins/scripts/prove_by_revert.sh <fix-commit> "<test command>"
```
Record a table in the PR: *fix reverted → journey that failed.* See [references/prove-by-revert.md](references/prove-by-revert.md).

When a journey uncovers a bug you can't fix in the same change, pin it as an **expected failure** (strict xfail / `test.todo` that fails when it starts passing) so it flips the day it's fixed.

### 7. Trim — only after the journeys exist
Delete or merge, with proof that nothing real was lost:
- near-duplicate tests (the same behaviour asserted by 3 layers) → keep the journey layer;
- dated "fix-of-the-day" files → merge by subject with one shared fixture;
- wording pins → one constants table + a check that each string still exists in the product;
- prompt-text pins and prompt hashes → replaced by behaviour evals (step 8).

Guard: product coverage must not drop, and every journey must still pass. Report test count, runtime and coverage before → after.

### 8. For AI features: test behaviour, not the prompt text
Pinning sentences in a system prompt proves the words exist, not that the model behaves. Write a small eval of scripted users with pass/fail rules and run it against the real model before any prompt change — [references/behaviour-evals.md](references/behaviour-evals.md). Run each case several times; models are not deterministic. Keep it out of CI (cost, flakiness); make it a required step for prompt PRs.

### 9. Close the loop in the release gate
Tests stop bugs before release; add cheap checks that catch what slipped after: duplicate side effects in the last 7 days, sends with no delivery receipt, old names still present in third-party copies, deploy actually running the new code. And never merge on red — turn on required checks. See [references/release-gate.md](references/release-gate.md).

### 10. Draw the before/after test map
Copy `assets/test-map.html` to `test-map.html` at the repo root and replace ONLY the JSON block inside it. One journey per door from step 1, one row per join on it, in the order a real user hits them. For each row:
- `before`: what the old suite did at that join. `bad` = no test reaches it, `weak` = a fake that can only succeed or a test that pins wording, `good` = the real path was already tested, failures included. Take this from the step 3 audit, not from memory.
- `after`: the same after this run. Mark `good` only when a journey test drives that join and passed prove-by-revert in step 6. If a found bug isn't fixed yet, add `found` and keep the row `weak`.
- `metrics`: real numbers from this run (bugs that got past the old suite, bugs the new tests found, test count before → after, coverage before → after). Leave out any you didn't measure. Never estimate.

Open the file in a browser and check it on a narrow screen. Its job is to show, in one look, where the old suite was blind and what checks each join now.

## Output
- `test-plan.md`: doors, joins, the scenario matrix with coverage marks.
- Journey tests + realistic fakes, each proven by revert.
- Pinned expected-failures for bugs found but not fixed.
- A trim PR with before/after numbers.
- For AI features: an eval runnable on demand.
- `test-map.html`: the before/after map of every journey and join (step 10).

## Anti-patterns this skill exists to stop
- "Coverage is 95%, so the tests are fine."
- A stub that can only succeed, standing in for the exact thing that broke.
- A test that replaces the real step with `return "ok"`.
- Testing one call when users make two.
- "Sent" meaning "the gateway accepted it".
- Writing a setting before reading the code that reads it.
- Fixing the function you found first instead of the path the feature flag actually routes to.
- A new test nobody has seen fail.
