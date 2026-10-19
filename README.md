# dev-skills

Agent skills I use to build software with AI coding agents (Claude Code, Codex, Cursor and others that read `SKILL.md`). Each skill is a folder under `skills/` with a `SKILL.md` and the references and scripts it needs.

## Skills

| Skill | What it does |
|---|---|
| [test-the-joins](skills/test-the-joins/SKILL.md) | Builds tests from how real users actually move through the code. Reads the codebase as a graph (graphify), maps every way users and other systems enter it, and turns each path into journey tests — the happy path **and** the unknown ones: retries, second sessions, restarts mid-step, providers that accept then fail, settings written under one key and read under another. |

## Why test-the-joins exists

I had thousands of green tests and high coverage, and I still shipped bugs every week. In one week:

- a lead's booking alert never reached the owner because the booking arrived on a *second* save;
- alerts showed "sent" while the messaging provider had accepted and then dropped them;
- the same meeting was booked twice when a chat restarted in a new session;
- a setting was written under one key while the code read another;
- a fix landed in the function I found first, not the path a feature flag actually used.

The modules that broke were 96–100% covered. Every bug sat at a **join** — between two calls, two sessions, two services, a writer and a reader — and every test faked exactly that join with a stub that could only succeed.

So I flipped the order: **read the code first (with a code graph) to see how real users will use it, then test every path — happy and unknown.** After one pass the suite had fewer tests, ran faster, and the new journey tests failed on every one of that week's bugs when I put them back. They also found five more real bugs on the first run.

Read the [principles](PRINCIPLES.md) — fourteen rules, short enough to keep in your head.

## Install

Copy the skill folder into your agent's skills directory, e.g. for Claude Code:

```bash
git clone https://github.com/HIMMAND/dev-skills
cp -r dev-skills/skills/test-the-joins ~/.claude/skills/
```

Or with the [skills CLI](https://www.npmjs.com/package/skills): `npx skills@latest add HIMMAND/dev-skills/test-the-joins`

`test-the-joins` uses [graphify](https://github.com/Graphify-Labs/graphify) (Apache-2.0) to read the codebase: `uv tool install graphifyy`.

## Using it

Ask your agent things like:

- "My tests are green but bugs keep shipping — run test-the-joins on this repo."
- "Map the doors and joins for the checkout flow and write journey tests."
- "Audit the test suite: which fakes can't fail, which tests only pin wording?"
- "Prove these new tests by reverting the fix."

## License

MIT
