# Scenario map: happy, unhappy, unknown

Use this after graphify has shown you the path from a door (route, webhook, job, page) to its side effects. For every **join** on that path, walk down this list and write one line per scenario that can happen. Skip the ones that truly can't — but say why in one word.

## How to find the joins with graphify
```bash
graphify explain "handleCheckout()"          # what it calls, who calls it
graphify path "handleCheckout" "sendReceipt"  # the chain between a door and a side effect
graphify query "who reads the setting reminder_template" --budget 1200
```
A join is any step where control or data leaves the function you're looking at and comes back later or elsewhere:
- a call to a third party (payments, messaging, email, calendar, CRM, LLM);
- a write that someone else reads later (a DB row, a queue message, a cache, a config/setting);
- a retry or job boundary (anything that can run twice);
- a lock / idempotency / dedupe key;
- a feature flag or plan check that routes to a different path;
- a value copied outside your system (a template registered at a provider, a CRM field, an exported sheet).

## The matrix

| Kind | Scenario | Question to answer |
|---|---|---|
| **Happy** | The intended path | What exactly does the person on the far end receive? |
| Unhappy | Provider down / timeout | Retried? Bounded? Surfaced to a human? Never silently "done"? |
| Unhappy | Provider rejects | Is the rejection detected even when it arrives as HTTP 200/201? |
| Unhappy | Invalid / partial input | Saved what's valid, refused what isn't, no crash? |
| Unhappy | Permission / plan / tenant | Blocked on the server, not only hidden in the UI? |
| **Unknown** | **Same event twice** (webhook redelivery, double click, retry) | Exactly one side effect? |
| Unknown | **Two passes** (fast save, later save with more info) | Does the later pass add without wiping, and do things that should happen once the info is known still happen? |
| Unknown | **Second session / tab / device** for the same person | One booking/charge/message per *person + thing*, not per session? |
| Unknown | **Retry after partial success** | Do completed steps stay done and skipped steps get another chance? |
| Unknown | **Process dies mid-step** (deploy, OOM, crash) | After the lease/lock goes stale, exactly one delivery? |
| Unknown | **Accepted, then failed** (async delivery status) | Recorded as failed / "not confirmed", not "sent"? |
| Unknown | **Writer and reader disagree** on a value's key or shape | Test from a real stored row through the real reader. |
| Unknown | **Two writers, one record** | Merge, never replace — a save that doesn't know a field keeps it. |
| Unknown | **Flag routes elsewhere** | Is the fix in the path the flag actually takes for this tenant? |
| Unknown | **Copied value outside your DB** (rename) | Does the far end show the new value? |
| Unknown | **Stale state** (expired trial, expired token, past date) | Does the system fail closed and tell someone? |
| Unknown | **Concurrency** (two requests at once) | Lock / transaction / unique key holds? |
| Unknown | **Time** (time zones, quiet hours, end of month, DST) | Correct local time for the *receiver*? |
| Unknown | **Shared identifiers** (one phone for two people, one account for two orgs) | Never merges two people / leaks between tenants? |
| Unknown | **Hostile input** (prompt injection, crafted IDs) | Can user text change *whose* data is loaded? (It must not.) |

## Writing a scenario line
> *Lead books a meeting in chat; the chat ends before the booking is saved; a background pass saves it from the transcript; the browser then re-sends its own copy without the time.* → **Far end:** one calendar event, the confirmation carries the link, the owner is alerted once with the booking, the record still shows the booking afterwards.

Each line becomes one journey test (or one row of a table-driven test).
