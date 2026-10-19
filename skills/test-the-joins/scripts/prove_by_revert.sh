#!/usr/bin/env bash
# Prove a test by putting the bug back.
#
#   prove_by_revert.sh <fix-commit> "<test command>"
#
# Reverts ONLY the non-test files changed by <fix-commit> in the working tree,
# runs the test command (expects it to FAIL), then restores those files.
# Exit 0 = proven (the test failed without the fix and the tree is restored).
# Exit 1 = NOT proven (the test still passed without the fix: it doesn't reach the join).
# Exit 2 = usage / dirty tree.
set -uo pipefail

FIX="${1:-}"; CMD="${2:-}"
if [[ -z "$FIX" || -z "$CMD" ]]; then
  echo "usage: $0 <fix-commit> \"<test command>\"" >&2; exit 2
fi
git rev-parse --verify --quiet "$FIX^{commit}" >/dev/null || { echo "unknown commit: $FIX" >&2; exit 2; }

# Product files only: skip anything that looks like a test or fixture.
FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(git diff --name-only "$FIX^" "$FIX" | grep -vE '(^|/)(tests?|__tests__|fixtures)/|(^|/)test_[^/]*\.py$|_test\.py$|\.(test|spec)\.(t|j)sx?$')
if [[ ${#FILES[@]} -eq 0 ]]; then echo "no product files in $FIX" >&2; exit 2; fi
if ! git diff --quiet -- "${FILES[@]}"; then
  echo "uncommitted changes in files the fix touched; commit or stash them first" >&2; exit 2
fi

restore() { git checkout -q HEAD -- "${FILES[@]}" 2>/dev/null; }
trap restore EXIT

echo "reverting product files of $FIX:"; printf '  %s\n' "${FILES[@]}"
git show "$FIX" -- "${FILES[@]}" | git apply -R --whitespace=nowarn || { echo "could not reverse-apply $FIX on this tree" >&2; exit 2; }

echo "running: $CMD"
if bash -c "$CMD"; then
  echo "NOT PROVEN: tests still pass with $FIX reverted — they don't reach the join." >&2
  exit 1
fi
echo "PROVEN: tests fail with $FIX reverted (restoring files)."
exit 0
