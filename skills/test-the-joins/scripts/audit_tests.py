#!/usr/bin/env python3
"""Audit a test suite for the patterns that let real bugs through a green suite.

Usage:  python3 audit_tests.py <repo-root> [--json] [--top N]

Heuristics (read the hits, don't trust them blindly):
  always_succeeds   a stub of a boundary that can only succeed
                    (returns an id / ok / claimed: True / resolved value with ok)
  constant_step     a real step replaced by `return "ok"` or a lambda returning "ok"
  wording_pin       assert on a long literal string (>= 40 chars); skipped when the line
                    or the line above carries `test-the-joins: exact` (wording IS the behaviour)
  source_pin        a test that reads product source files and regex-matches them
  prompt_hash       a test that hashes rendered text (sha256/md5) to pin it
  sleep             real-time sleeps in tests (slow + flaky; use a fake clock)

Pure standard library. Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

TEST_FILE = re.compile(r"(^test_.*\.py$|_test\.py$|\.(test|spec)\.(t|j)sx?$|\.(test|spec)\.m?js$)")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", "__pycache__", ".turbo", "coverage"}

PATTERNS = {
    "always_succeeds": [
        re.compile(r"""return_value\s*=\s*\{\s*["'](id|ok|claimed|success|status)["']"""),
        re.compile(r"""return\s*\{\s*["']claimed["']\s*:\s*True"""),
        re.compile(r"""mockResolvedValue\(\s*\{\s*(ok|id|success|claimed)\s*:"""),
        re.compile(r"""return\s*\{\s*["']key["']\s*:\s*\{\s*["']id["']"""),
        re.compile(r"""AsyncMock\(\s*return_value\s*=\s*["']ok"""),
    ],
    "constant_step": [
        re.compile(r"""^\s*return\s+["']ok["']\s*$"""),
        re.compile(r"""lambda\s*[^:]*:\s*["']ok["']"""),
        re.compile(r"""=>\s*["']ok["']"""),
    ],
    "wording_pin": [
        re.compile(r"""assert[^\n]*==\s*["'][^"'\n]{40,}["']"""),
        re.compile(r"""assert\.(equal|strictEqual)\([^\n]*["'`][^"'`\n]{40,}["'`]"""),
        re.compile(r"""expect\([^\n]*\)\.toBe\(\s*["'`][^"'`\n]{40,}["'`]"""),
    ],
    "source_pin": [
        re.compile(r"""readFileSync\([^\n]*\.(t|j)sx?["'`]"""),
        re.compile(r"""open\([^\n]*\.(py|ts|tsx)["'][^\n]*\)\.read\(\)"""),
    ],
    "prompt_hash": [
        re.compile(r"""createHash\(\s*["'](sha256|md5|sha1)["']\s*\)"""),
        re.compile(r"""hashlib\.(sha256|md5|sha1)\("""),
    ],
    "sleep": [
        re.compile(r"""\btime\.sleep\(\s*[0-9.]+\s*\)"""),
        re.compile(r"""\basyncio\.sleep\(\s*[1-9][0-9.]*\s*\)"""),
        re.compile(r"""setTimeout\(\s*r(esolve)?\s*,\s*[1-9][0-9]{3,}\s*\)"""),
    ],
}

MARK = "test-the-joins: exact"

BOUNDARY_HINTS = re.compile(
    r"(send|post|deliver|notify|claim|lock|idempot|charge|pay|webhook|template|calendar|crm|stripe|twilio|"
    r"sms|whatsapp|email|smtp|openai|llm|fetch|http)",
    re.I,
)


def iter_test_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".worktrees")]
        for name in filenames:
            if TEST_FILE.search(name):
                yield os.path.join(dirpath, name)


def scan(root: str):
    hits = defaultdict(list)          # kind -> [(file, line_no, line)]
    per_file = defaultdict(Counter)   # file -> Counter(kind)
    files = 0
    for path in iter_test_files(root):
        files += 1
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        rel = os.path.relpath(path, root)
        for i, line in enumerate(lines, 1):
            for kind, regs in PATTERNS.items():
                if any(r.search(line) for r in regs):
                    if kind == "wording_pin" and (MARK in line or (i > 1 and MARK in lines[i - 2])):
                        continue
                    if kind == "always_succeeds":
                        window = " ".join(lines[max(0, i - 4): i + 1])
                        if not BOUNDARY_HINTS.search(window):
                            continue
                    hits[kind].append((rel, i, line.strip()[:160]))
                    per_file[rel][kind] += 1
    return files, hits, per_file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    files, hits, per_file = scan(a.root)
    if a.json:
        json.dump({"test_files": files, "hits": {k: v for k, v in hits.items()}}, sys.stdout, indent=1)
        return 0
    print(f"test files scanned: {files}\n")
    print("kind              hits  files")
    for kind in PATTERNS:
        n = len(hits[kind])
        f = len({h[0] for h in hits[kind]})
        print(f"{kind:<17} {n:>5}  {f:>5}")
    print("\nfiles with the most hits:")
    ranked = sorted(per_file.items(), key=lambda kv: -sum(kv[1].values()))[: a.top]
    for rel, c in ranked:
        print(f"  {sum(c.values()):>4}  {rel}  " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
    for kind in ("always_succeeds", "constant_step"):
        if hits[kind]:
            print(f"\nexamples of {kind} (the fakes that can't fail):")
            for rel, i, line in hits[kind][:8]:
                print(f"  {rel}:{i}  {line}")
    print("\nNext: for each boundary above, use a stateful fake that can fail "
          "(see references/realistic-fakes.md), and drive the join in a journey test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
