# Modifications (holler-roles)

This kit is pstack-claude at `356c6e0f978df729eb16f227d795f34d221c5aad` (MIT), path `plugins/pstack`, modified by
72o Labs as below. Each change is recorded in `patches/upstream/<item>.patch` as a diff from the pristine upstream
file at that commit to the kit file. Files not listed here are unchanged.

1. `skills/why/SKILL.md`: the frontmatter `description` trimmed; the body is unchanged (`why.patch`).
2. Eight playbooks under `skills/poteto-mode/playbooks/` (investigation, bug-fix, feature, refactoring, perf-issue,
   prototype, session-pickup, pause-safely) are also published as skills: `skills/<name>/SKILL.md` = new frontmatter
   (`name`, `description`) + a preamble + the playbook body, unchanged (`<name>.patch`, from
   `plugins/pstack/skills/poteto-mode/playbooks/<name>.md`). The original playbook files stay, unchanged.
3. `skills/figure-it-out/SKILL.md`: frontmatter `description` replaced and the same preamble inserted; the body is
   unchanged (`figure-it-out.patch`).
4. The preamble (72o Labs text, MIT like the rest of this kit) tells the agent where the principles index and the
   reference files are, relative to the skill folder.
5. Parts of the upstream tree are not shipped (hooks, setup-pstack, automate-me, poteto-help, babysit and the
   PR-automation playbooks' dependencies, the orchestrate store and watchers, reflect except
   `scripts/claude-project-dir.mjs`, other harness manifests). See PROVENANCE.md.
6. At build time a consumer may add `disable-model-invocation: true` and `user-invocable: false` to the frontmatter of
   skills it does not list, or an `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. Those flags
   change no instruction text.
