# Prove a test by putting the bug back

1. Write the journey with the fix in place. It passes.
2. Revert only the product files of the fix (keep the new test):
   ```bash
   scripts/prove_by_revert.sh <fix-commit-sha> "pytest -q tests/test_lead_journey.py -k booking"
   ```
   The script reverts the non-test files changed by that commit, runs the command, expects a **failure**, then restores everything.
3. Record it in the PR:

| Fix reverted | Journey that fails | How it fails |
|---|---|---|
| `abc1234` once-per-booking key | `test_second_session_books_once` | 2 calendar events |
| `def5678` skipped step releases its claim | `test_skip_then_later_save_confirms` | confirmation stays "skipped" |

If the test still passes with the fix reverted, the test is wrong (it doesn't reach the join) — fix the test, not the table.

One commit holds several rules (a whole feature)? Reverting it only proves the tests fail together. Break each rule on its own:
```bash
scripts/prove_by_mutation.sh src/lib/lookup.ts 'if (!namesSource(quote)) return false' 'if (false) return false' "npm test -- lookup"
```
One line per rule in the table. A mutation that leaves the tests green means that rule has no test.

No fix to revert (testing an existing behaviour)? Same tool: break the behaviour with `prove_by_mutation.sh` (flip a condition, drop a call). Same rule: you must see it fail once.

`prove_by_revert.sh` keeps tests, fixtures and eval scripts (`evals/`, `eval-*`, `*.eval.*`) in place. Add more with `PROVE_EXCLUDE='<regex>'`.
