# Principles for testing what users actually do

Short enough to keep in your head. Drop it into `CLAUDE.md` / `AGENTS.md` if you want an agent to follow it everywhere.

1. **Test the joins, not just the parts.** Bugs live where one piece hands off to another: the second call, the retry, the restart, the other service. If no test drives the join, the join is untested — whatever the coverage number says.

2. **Read the code before you test it.** Map how a real user enters and moves through the system (use a code graph, e.g. graphify). Tests come from those paths, not from the list of functions.

3. **Every path has three cases: happy, unhappy, unknown.** Happy is what you built. Unhappy is what you expect to go wrong. Unknown is what ships as a bug: twice, half-done, out of order, stale, concurrent, from a second session, after a restart.

4. **A fake must be able to fail like the real thing.** A stub that always returns "OK" is a test of your hopes. Fakes model real states: accepted-then-failed, in progress, stale, rejected with a 200.

5. **Fake only at the outer edge.** Replace the third party's HTTP call, never a step of your own code. A test that swaps your real step for `return "ok"` cannot catch your bug.

6. **"Sent" means delivered.** A gateway accepting a message is not the person receiving it. Record and test the delivery result.

7. **Find every reader before you write.** A setting, a field, a cache key: look up who reads it and in what shape, and write that. Then test from a real stored row through the real reader.

8. **Find every copy before you rename.** Values get copied outside your database — third-party templates, CRMs, caches, exports. A rename is done when the person on the far end sees the new value.

9. **Two writers, one record: merge, don't replace.** When two parts of the system fill the same record with different knowledge, a later save must keep what it doesn't know.

10. **Prove a test by putting the bug back.** If you never saw it fail, it proves nothing.

11. **Assert what the far end receives.** One confirmation, the right person alerted, the honest "not confirmed" — not which internal function ran.

12. **Pin behaviour, not wording.** Tests that check exact strings, source text or prompt hashes break on a rename and pass on a real bug.

13. **For AI, test what it does.** Scripted users, pass/fail rules, several runs each — before every prompt change.

14. **Merge only on green.** Turn on required checks. A pipeline that prints a red result and merges anyway is not a gate.
