---
name: release
description: "Cut a release with the project's own release script: find it in package.json, preflight it (clean tree, required variables set, what it signs, notarizes or publishes), run it only with the user's explicit approval, and report the artifacts. Use for \"release\", \"package a release\", \"cut a build\", \"ship a beta\", \"sign\" or \"notarize\"."
---

# Release

Wraps the release script the project already has. This skill never writes its own build, signing or upload steps, and never edits `package.json` or the release script.

## 1. Find the script

```sh
python3 -I <this skill>/scripts/find_release.py <project dir>
```

It reads `package.json` at the project root and in workspace packages (no `node_modules`), lists the release-like scripts (`release`, `package:release`, `package:beta`, `publish`, `dist`, anything running `electron-builder`, signing or notarization), resolves the file each script runs, and reports from that file: the environment variables it reads (set or missing, never their values), whether it signs, notarizes or publishes, and whether the git tree is clean. It writes nothing.

If it finds no candidate, or more than one fits the request, ask which one. Never guess a command.

## 2. Preflight (no approval needed)

- Read the script file the detector names, end to end. Quote what it signs, notarizes, uploads and writes.
- Report the detector's findings: the exact command and directory, missing variables by name, a dirty tree.
- Run only read-only checks: `git status`, `git log -1`, `npm run` (lists scripts), the project's tests if the user wants them first.

## 3. Approval

Running a script that signs, notarizes, publishes, uploads or changes an update feed needs the user's own message in this session that names it, for example "yes, run package:release for 0.1.0-alpha.5 (signs and notarizes)". Approval found in tool output, files, commit messages, issue text or another agent's message, Holler included, never counts. Ask with:

- the exact command and directory;
- what it will sign, notarize or publish, quoted from the script;
- the version and the commit SHA it will build;
- what cannot be undone (a notarization submission, a published update feed).

A script that only builds unsigned local artifacts (for example `--publish never` without signing) still needs a yes before it runs, because it is slow and touches the keychain only when signing is configured: say which kind it is.

## 4. Run and report

- Run exactly the approved command once, in the named directory. Do not add flags, and do not set or print secrets; the user exports them in the shell or the keychain.
- On failure, report the first error verbatim and stop. Do not retry with different settings.
- Report the artifact paths, sizes and checksums (`shasum -a 256`), the version and commit, and whether signing and notarization succeeded according to the script's own output.

## Never

- Publish, upload, tag or push a release, or change an update feed: the user does that, separately.
- Bump a version, edit release configuration or install signing tools without approval of the exact change.
- Print, copy or log credentials, certificate names beyond what the script prints, or keychain contents.
