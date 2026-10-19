# Journey test template

A journey replays one real path through the real code, from the door to the far end, with fakes only at the outer edge.

```python
def test_booking_saved_late_still_confirms_once(journey):
    """Door: chat ends before the booking is saved.
    Real-world order (from production, 2026): fast save → background pass saves the
    booking from the transcript → the browser re-sends its own copy without the time.
    Far end: one calendar event, one confirmation with the link, owner alerted once
    with the booking, the record still shows the booking."""
    # 1. arrange — real recorded payloads (anonymised), realistic fakes
    chat = journey.load_fixture("replay/booking_said_not_saved.json")
    gateway = journey.gateway(mode="ok")
    calendar = journey.calendar()

    # 2. act — drive the REAL entry points in the order users/systems really call them
    journey.post("/lead", chat.fast_save)            # no booking yet
    journey.run_background_pass(chat.transcript)     # finds and saves the booking
    journey.post("/lead", chat.browser_resend)       # arrives later, without the time
    journey.drain_jobs()

    # 3. assert — what the far end received, not which function ran
    assert len(calendar.events) == 1
    assert [m for m in gateway.sent if m.kind == "confirmation"] == [ANY_WITH(link=calendar.events[0].link)]
    assert journey.alerts_to_owner() == [ANY_WITH(booking=calendar.events[0].start)]
    assert journey.record(chat.person).booking == calendar.events[0].start
```

## Checklist for a good journey
- [ ] Named after what the user does, not after the function.
- [ ] Docstring says the real-world order and the far-end outcome.
- [ ] Uses the real entry points, in the real order (including the second/late call).
- [ ] Fakes only third-party edges; fakes can fail (see realistic-fakes.md).
- [ ] Data from a recorded real case, anonymised (no real names, numbers, emails, tokens).
- [ ] Asserts counts (exactly one) and content at the far end.
- [ ] Proven: fails when the fix is reverted (see prove-by-revert.md).
