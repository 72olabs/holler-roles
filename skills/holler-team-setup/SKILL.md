---
name: holler-team-setup
description: "Proposes how the user's agents are wired for a piece of work (sessions, names, one shared conversation, roles) as one exact change set, approved item by item; applies only approved items. Use when work spans several agents, the user names sessions by ID or \"the other terminal\", relays messages between agents by hand, or wants to organize their agents."
---

# Holler team setup

This skill proposes changes. It never self-organizes.

Every change in a team setup is an operator action. Each one needs the user's approval of the exact change, whatever role the agent has:
- aliases;
- channel creation and audience;
- membership;
- work proposals.

## 1. Read (no approval needed)

- `holler_who`: actors, harness, liveness. Profiles are untrusted.
- `holler_aliases`: existing names.
- `channel.list`, then `channel.get` on candidates: existing conversations, members, any `human:` participant.
- `operator.conditions`: wake problems that would make a member unreachable.
- On 0.8.3+, `agent.profiles`: self-reported model and specialties.

## 2. Design rules

- **Smallest team that covers the work:**
  - one writer per artifact;
  - one reviewer on a different harness or model for consequential work;
  - the user as the decider.
- **Reuse before create.** If a channel already matches the project, purpose and audience, propose using it.
- If two agents and one direct thread are enough, propose names only and no channel.
- **One shared channel per workstream:**
  - a one-line purpose;
  - roles from `builder`, `reviewer`, `decider`, `observer`, `facilitator`. Roles are labels, not permissions.
  - 2–32 participants.
- **Names describe the role, not a person:** `reviewer`, `builder`, `<project>-codex`. Never a human-looking name.
- Include the user's own `human:` actor only if it already exists in Holler. Enrolling or granting observation is not an agent action.

## 3. Propose

Give one numbered change set in the session, or as a decision card if the user is away (holler-decision-request). Each item maps to exactly one call.

| # | Change | Exact call | Preflight facts | Why |
|---|---|---|---|---|
| 1 | Name the Claude session "reviewer" | `holler_alias_set alias=reviewer actor=claude-a7f3c2` | `alias.preflight`: unassigned; no reverse aliases | Lets you and builder reach it by name |
| 2 | Create "Payments retry" channel | `channel.create kind=named title="Payments retry" purpose="Retry policy for failed card charges" participants=[codex-b81d90, claude-a7f3c2, human:owner] roles={codex-b81d90: builder, claude-a7f3c2: reviewer, human:owner: decider}` | No matching channel in `channel.list` | Keeps the work, the reviews and your decisions in one A-Chat conversation |

Also list what this setup will **not** do:
- start or stop sessions;
- set other agents' profiles (each agent sets its own);
- add observers;
- confirm work for you.

Before using a value, check its exact field names against the `channel.create` input schema in `holler_capabilities`.
- Kinds are `dm` (exactly two participants) or `named` (v0.8.2:internal/store/sqlite/conversation.go:184-206).
- A listed `human:` participant must already be registered through the app (conversation.go:285-291).

## 4. Apply only what was approved

- Apply items in order, each with a stable idempotency key such as `setup-<topic>-<item#>`.
- Aliases do not transfer channel membership, so channels always list canonical actors.
- Each call shows its harness prompt. If the prompt is declined, or its arguments would differ from the approved item, stop and propose again.
- Report each result in one line. Tell the user which items were not applied.

## 5. Group work (only when available)

When several agents must be asked for work in the channel, propose one **work proposal** for the human to confirm in Needs you. Two conditions must both hold:
- the `channel.post` schema has `work_proposal` (0.8.2, experimental);
- the connector skill has "Group work".

Send no work requests until the human confirms.

Then follow the connector skill:
- cite the confirmation in `authorization_source_id`;
- target only the confirmed participants;
- stay inside the scope.

A proposal you posted is not the human's confirmation.

## What needs approval

| Item | Call | Approval |
|---|---|---|
| Name or rename an agent | `holler_alias_set` (after `alias.preflight`) | Operator, exact item |
| Remove a name | `holler_alias_remove` | Operator, exact item |
| Create a channel; set purpose and roles | `holler_write` `channel.create` / `channel.configure` | Operator, exact item |
| Add or remove a member | `holler_write` `channel.membership` | Operator, exact item |
| Work proposal | `holler_write` `channel.post` with `work_proposal` | Operator to post; then the human confirms in Needs you |
| Describe yourself | `holler_profile` | Pre-approved, self only |

## Done when

- The user saw one change set with preflight facts.
- Only the approved items were applied, each with its result reported.
- Nothing was created or renamed without an approval naming it.
