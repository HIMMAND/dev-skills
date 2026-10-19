# Auditing an existing suite

Run `scripts/audit_tests.py <repo>` for the mechanical part, then answer these by hand.

## 1. Inventory by kind
Count tests per kind: pure unit · route/handler with mocked internals · harness with stateful fakes · contract against captured real payloads · replay of real cases · real-provider (staging). A healthy suite has a thin but real top: a handful of journeys and replays per door.

## 2. What do the fakes fake?
For each external boundary (gateway, lock/claim store, CRM, LLM, database), list the test files that stub it and whether the stub **can fail**. Flag:
- stubs that only ever return success / an id;
- lock stubs that only ever say "claimed";
- a real pipeline step replaced by a constant (`return "ok"`).
These are the exact places this week's bug will hide.

## 3. Coverage — and why it lies
Measure product-only coverage (exclude test files). Then look at the modules your recent bugs came from: if they are 95%+ covered, coverage is not your gap — **scenario shape** is. Line coverage counts a line run in a unit test as "tested" even if no test ever runs it twice, after a restart, or with a failing provider.

## 4. Pinned wording
Flag tests that assert exact prose (log/skip reason strings, UI copy, prompt sentences), read source files and regex them, or hash rendered prompts. Replace with: a constants table + a check that each value still exists in the product; behaviour assertions; evals for AI.

## 5. Dead code
For every candidate, confirm **both** with `graphify explain "<symbol>"` (no inbound edge) **and** a text search across every repo that could call it (including scripts, cron/launchd, CI workflows, runbooks, other services). The graph can be stale; text search can miss dynamic calls. Need both before deleting.

## 6. Bug replay
For each real bug of the last month: which layer would have caught it, and why didn't the suite? Common answers: single call tested, second call not; the stub could only succeed; the setting was fed in the reader's shape by hand instead of from a stored row; the fix was tested in the function the flag doesn't route to.
