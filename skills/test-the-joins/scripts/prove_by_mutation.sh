#!/usr/bin/env bash
# Prove a test by breaking ONE rule, not reverting a whole commit.
#
#   prove_by_mutation.sh <file> '<exact code>' '<broken code>' "<test command>"
#
# Swaps the first exact (literal, not regex) match of <exact code> in <file> for
# <broken code>, runs the test command (expects it to FAIL), then restores the file.
# Exit 0 = proven (the tests caught the broken rule; file restored).
# Exit 1 = NOT proven (tests still pass with the rule broken: nothing tests it).
# Exit 2 = usage / file not clean / code not found.
set -uo pipefail

FILE="${1:-}"; FROM="${2:-}"; TO="${3-}"; CMD="${4:-}"
if [[ -z "$FILE" || -z "$FROM" || -z "$CMD" ]]; then
  echo "usage: $0 <file> '<exact code>' '<broken code>' \"<test command>\"" >&2; exit 2
fi
[[ -f "$FILE" ]] || { echo "no such file: $FILE" >&2; exit 2; }
if git ls-files --error-unmatch "$FILE" >/dev/null 2>&1 && ! git diff --quiet -- "$FILE"; then
  echo "uncommitted changes in $FILE; commit or stash them first" >&2; exit 2
fi

BACKUP="$(mktemp)"; cp "$FILE" "$BACKUP"
restore() { cp "$BACKUP" "$FILE"; rm -f "$BACKUP"; }
trap restore EXIT

FROM="$FROM" TO="$TO" python3 - "$FILE" <<'PY' || exit 2
import os, sys
p = sys.argv[1]; src = open(p, encoding="utf-8").read()
frm, to = os.environ["FROM"], os.environ["TO"]
if frm not in src:
    sys.stderr.write(f"code not found in {p}: {frm[:80]!r}\n"); sys.exit(2)
open(p, "w", encoding="utf-8").write(src.replace(frm, to, 1))
PY

echo "broke $FILE: ${FROM:0:70} -> ${TO:0:70}"
echo "running: $CMD"
if bash -c "$CMD"; then
  echo "NOT PROVEN: tests still pass with this rule broken. Nothing tests it." >&2
  exit 1
fi
echo "PROVEN: tests fail with this rule broken (restoring $FILE)."
exit 0
