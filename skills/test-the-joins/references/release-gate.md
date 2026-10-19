# Release gate: catch what tests can't

Tests stop known bugs before release. These cheap, read-only checks catch what still slips through — run them after every deploy (a `smoke` script) and fail loudly.

- **The new code is actually running.** Byte-compare a few changed files inside the running container with the released commit. "CI green" and "deploy job succeeded" have both been seen with the old container still running.
- **No duplicate side effects** in the last 7 days (same person + same slot booked twice, same message sent twice).
- **Sends without a delivery receipt** in the last 24 h (accepted but never confirmed delivered).
- **Copies outside your DB match** (a renamed value still present in a provider-side template, a CRM field, a sheet header).
- **Config matches reality** (the number/account a setting says is the one actually connected).
- **What's queued for release** (commits on staging not yet in prod), listed every time — including other people's.

And the one that isn't a test at all: **required checks on the branches you merge into.** A pipeline that shows a red check and merges anyway is not a gate.
