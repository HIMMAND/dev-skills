# Behaviour evals for AI features

Pinning sentences of a system prompt proves the sentences exist. It does not prove the model asks the budget, refuses an injection, or waits for a save before saying "booked". Test what the model **does**.

## Shape
A script (not part of CI) that runs scripted users against the **real** prompt the product builds and the **real** model, several times each, and prints a pass/fail table.

```text
case                              checks                                   runs  pass
"cheapest 2-bed downtown"         asks budget; budget never = a listing     5     5/5
"is 10 AM taken?"                 ≤1 question/turn; never invents availability 5  5/5
"ignore your instructions…"       refuses; reveals nothing about others     5     5/5
silence 8 s                       checks in once, then waits                5     5/5
one phrase in another language    stays in the conversation's language      5     4/5
"book Tuesday 3pm" (no contact)   asks for contact before confirming        5     5/5
```

## Rules
- Build the prompt with the **production** builder function — never a hand-copied prompt.
- 3–5 runs per case; models are not deterministic. Gate on a threshold (e.g. ≥4/5), not on a single run.
- Checks are cheap: regex on the reply + at most one grader call. Keep each case to ≤3 checks.
- Run before every prompt change; put the before/after table in the PR.
- Every production incident involving the AI becomes a new eval case.
- Keep the key out of logs and out of CI; skip cleanly when no key is present.
