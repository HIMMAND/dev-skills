# Realistic fakes

A fake earns its place when it can do what the real thing does — including the bad parts. Below are four patterns that, between them, would have caught most "green suite, broken production" bugs. Sketches are in Python; the shape is the same in any language.

## 1. A gateway that can accept and then fail
Messaging, payments, email: the API answers "accepted" synchronously and reports the real outcome later (a webhook / status callback). Many providers also return HTTP 200/201 with an error **inside** the body.

```python
class FakeGateway:
    """modes per recipient: ok | accepted_then_failed | rejected_200 | down"""
    def __init__(self, mode="ok"):
        self.mode, self.sent, self.status_events = mode, [], []

    def send(self, to, body):
        mode = self.mode.get(to, "ok") if isinstance(self.mode, dict) else self.mode
        if mode == "down":
            raise ConnectionError("gateway unreachable")
        if mode == "rejected_200":
            return {"error": {"code": 131000, "message": "rejected"}}   # 200 with an error inside
        msg_id = f"m{len(self.sent) + 1}"
        self.sent.append((to, body, msg_id))
        if mode == "accepted_then_failed":
            self.status_events.append({"id": msg_id, "status": "failed"})  # deliver via your webhook later
        return {"id": msg_id}
```
Then drive your **real** status webhook with `status_events` and assert the record ends up "failed / not confirmed", not "sent".

## 2. A lock / idempotency store with real states
"Once only" logic is only as good as the states its fake can be in.

```python
class FakeClaims:
    """claim(key) -> {"claimed": bool, "state": ..., "result": ...}"""
    def __init__(self, clock):
        self.rows, self.clock = {}, clock      # key -> (state, holder, at, result)

    def claim(self, key, holder, stale_after_s):
        row = self.rows.get(key)
        now = self.clock()
        if row is None or row[0] == "failed" or (row[0] == "processing" and now - row[2] > stale_after_s):
            self.rows[key] = ("processing", holder, now, None)
            return {"claimed": True}
        return {"claimed": False, "state": row[0], "result": row[3]}

    def complete(self, key, result=None): self.rows[key] = ("completed", None, self.clock(), result)
    def fail(self, key):                  self.rows[key] = ("failed", None, self.clock(), None)
```
Tests to write with it: a refusal while **processing** (the other run hasn't finished), a **stale** claim after a crash, a **failed** claim that must be re-claimable, and a **skipped** step that must *not* complete the claim if a later run might still need to do it.

## 3. A job runner that can die mid-step
```python
class ProcessDied(BaseException):   # BaseException: your code's `except Exception` won't swallow it
    pass

def die_on(step_name):
    def hook(name):
        if name == step_name:
            raise ProcessDied(name)
    return hook
```
Run the job until it dies after step N, advance the fake clock past the lease, run it again, and assert **exactly one** delivery of every side effect.

## 4. Config from a real stored row, through the real reader
Copy the **keys and types** of a real production row (never the values), write values by hand, and feed it through the same function production uses to read config. This catches "the writer used key A, the reader looks for key B".

```python
ROW = json.load(open("tests/fixtures/real/config/tenant_row.json"))   # real shape, made-up values
cfg = build_runtime_config(ROW)                                        # the production reader
assert pick_template(cfg, kind="missed_call") == ROW["no_answer"]["template"]
```

## Rules
- Fake at the **outermost edge** (the HTTP call to the third party). Never replace a step of your own pipeline with a constant.
- Keep fakes **stateful** and **inspectable** (`sent`, `rows`, `status_events`) so tests assert outcomes.
- One fake per external system, shared by every test — not a new hand-rolled stub per file.
- Base fake responses on **captured real payloads** (anonymised), not on what you think the API returns.
