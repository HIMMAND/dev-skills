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

No fix to revert (testing an existing behaviour)? Break the behaviour by hand (flip a condition, drop a call), run, restore. Same rule: you must see it fail once.
