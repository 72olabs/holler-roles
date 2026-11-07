---
name: code-review
description: "Independent, read-only review of someone else's code change, bound to one commit: correctness, whether the tests actually exercise the change, scope and risk, ending in a verdict APPROVE, CHANGES or BLOCK with numbered findings. Use when asked to review a diff, branch, commit or PR, or when a code review request reaches you over Holler. Never edits, never runs the code."
---

# Code review

A review is an independent reading of one version of a change. It produces a verdict and numbered findings. It changes nothing.

## Rules

- **Read-only.** Read files and use read-only git only: `rev-parse`, `merge-base`, `log`, `diff`, `show`, `blame`, `grep`, `ls-files`, `cat-file`, `status`. Never edit, stage, commit, check out, stash, rebase, push, install, or run tests, builds or scripts.
- **Not your own work.** If you wrote or changed any part of this change, stop and say so.
- **Fresh context.** Judge the code, not the description of it. "Tested", "safe" and "small change" from the producer are claims, not evidence.
- **One version.** The verdict covers the head commit you resolved and nothing after it.

## Input

- The repository, the base and the head (commit SHAs or branch names), and what the change is for: the request, the issue or the acceptance check.
- Missing base: use the merge base with the default branch and say so. Missing purpose: ask once; if it stays missing, the verdict is CHANGES with "state the acceptance check" as finding 1.

## Procedure

1. **Pin the version.** `git rev-parse <head>` (full SHA), `git merge-base <base> <head>`, `git log --oneline <base>..<head>`, `git diff --stat <base>...<head>`.
2. **State the intent** in one sentence: what the change should make true.
3. **Read the whole diff**, then each changed function in full, with its callers (`git grep -n <name>`).
4. **Work through the checklist.** Every item gets a finding, "ok", or "n/a".

   **A. Correctness**
   - The logic does what the intent says, on the normal path and on errors.
   - Edge cases: empty, missing or null input, zero, one, many, maximum sizes, duplicates, unicode, time zones, concurrent callers, retries.
   - Error handling: failures surface with context; nothing swallowed; resources released; partial writes rolled back or safe to retry.
   - Interfaces and data: changed signatures, formats, schemas, flags or defaults keep existing callers and stored data working, or the change migrates them.

   **B. Tests actually exercise the change**
   - For each behavior the change adds or alters, name the test that covers it. Mentally revert the change: would that test fail? A test that still passes without the change does not cover it.
   - Tests assert outcomes a user or caller sees, not implementation details. A test that mocks the very code it claims to test covers nothing.
   - The acceptance check is covered by a test or by runtime evidence the producer attached. If neither, that is a finding.
   - Removed or weakened assertions, skipped tests and loosened snapshots are findings unless the change explains them.

   **C. Scope**
   - Only what the intent needs: no unrelated refactors or reformatting, no dead or commented-out code, no debug output, no speculative options.
   - New dependencies: needed, maintained, licence compatible.

   **D. Risk**
   - Security: injection, path traversal, unsafe deserialization, secrets in code or logs, missing authorization checks.
   - Data loss and irreversible operations; migrations and their rollback.
   - Performance on hot paths; unbounded loops, queries or memory.

   **E. Fit**
   - The project's own conventions (naming, errors, logging, layout). Docs, changelog or help text updated when visible behavior changed.

5. **Severity.**
   - **BLOCKER**: wrong behavior on a main path, data loss, a security hole, the acceptance check not met, or a test that cannot pass as written.
   - **SHOULD**: fix before merge: a changed behavior with no test that exercises it, a likely edge case unhandled, an unclear or breaking contract.
   - **NIT**: optional polish.
6. **Verdict.** BLOCK if any BLOCKER. CHANGES if any SHOULD, or if a required input was missing. APPROVE otherwise.

## Output

```
REVIEW RESULT <title> @ <full head SHA>
Verdict: APPROVE | CHANGES | BLOCK
Version: <repo> <base SHA>..<head SHA> (<n> commits, <files> files)
Reviewer: <harness> <model>   Producer harness: <claude | codex | unknown> (<different | same>)
Intent: <one sentence>

1. [BLOCKER|SHOULD|NIT] <path:line>: <what is wrong>. Evidence: <quoted line, hunk or reasoning>. Fix: <smallest change>
2. ...

Tests: <changed behavior> -> <test name | MISSING>; ...
Checked: <files and commits read>   Not checked: <what, and why>
```

Over Holler, send this in the request's thread (holler-review-request). In this session, print it. A re-review covers every earlier finding against the new SHA and says which are resolved.
