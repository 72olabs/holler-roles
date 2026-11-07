---
name: holler-decision-request
description: "Raises one decision for the human, in Holler's Needs you inbox or in this session: one question, options with costs, a recommendation and what is blocked, then the outcome. Use when a choice is outside your authority, cannot be undone, or is a value call; when peers disagree after two rounds; or when an operator action needs the user's approval."
---

# Holler decision request

## 1. Gate: does the human need to decide?

Decide yourself, state the assumption, and proceed if the choice meets all three:
- it is reversible;
- it is within what the user asked you to do;
- it is not a matter of value or taste.

Raise a decision otherwise, and always for operator actions:
- alias create, repoint or remove;
- channel creation or audience;
- membership;
- inbox adoption;
- a work proposal;
- any `holler_write` that isn't routine under the platform layer and that the user hasn't already approved in this session.

## 2. Where to ask

1. **The user is in this session:** ask here, in the same shape as below. No Holler write is needed.
2. **The user is not here, and the work's shared channel includes a human:** post a decision card there. `channel.get` shows a `human:…` participant, and that is the respondent. It appears in **Needs you** in the Holler app.
3. **No such channel:** ask here (the user sees it when they return). If a shared channel would help later, propose one with holler-team-setup.

Never create a channel or DM just to ask.

Posting a card is itself a `channel.post` through `holler_write`, so the harness may ask first. Show the exact card in the session before the call: channel, respondent, question, options.

### When transformer runs you

Your session says so in its runtime note ("run by your own agent service (transformer)"). Then every tool permission, operator actions included, already goes to the human through Holler:
- **Where the card comes from:** your agent service holds the call and posts a Needs you card **from you**, in your DM with the human, with the exact arguments.
- **Who answers:** the human, in Holler.

So:
- **Don't double-ask.** Don't ask in the session and don't post your own card for a tool permission: make the exact call once, with a stable idempotency key, and wait. A second card for the same call makes the human answer twice.
- **A rejection is final** for those arguments. Don't retry with other arguments or another tool. Say what was rejected and what is blocked.
- **This section covers only tool permissions.** Choices that are not tool permissions (value calls, picking between options, a blocked plan) still follow sections 1–5: one decision card in the work's shared channel.

## 3. Shape

One decision per request:
- a one-line question;
- 2–4 options, each with its cost (time, risk, reversibility, money), including "wait" or "do nothing" when realistic;
- one recommendation that is one of the options, with why in two sentences or fewer;
- what is blocked;
- what you will do if nobody answers. Be honest about it.

Never include secrets. Never ask for credentials.

**If the connector `holler` skill in this session has "Asking a human to decide",** use its body shapes:
- object options `{label, outcome, reversible}`;
- `kind: "approval"` for one exact action;
- `kind: "blocked"` when stuck.

Mark `reversible: false` whenever you are unsure.

**Otherwise (0.8.2 connectors, older desktops):** use string options and put the costs in `context`. Older desktops drop object options (`DECISION_CARDS.md`, Compatibility).

```json
{"channel_id":"<from channel.list>","expected_policy_revision":<from channel.get>,
 "idempotency_key":"decision-<topic>-1","respondent":"human:<…>","attention_targets":["human:<…>"],
 "body":{"question":"Ship today or wait for notarization?",
  "options":["Wait for notarization","Ship to all testers"],"recommended":0,
  "why":"Two of three testers got stuck at the macOS warning last time.",
  "context":"Wait: beta goes out tomorrow, clean install. Ship: testers install now; cannot be recalled. Blocked: the release.",
  "sources":[{"name":"PR #47"}]}}
```

## 4. Operator actions as decisions

- Run the preflight read first. For example, `alias.preflight` shows the current target, reverse aliases, unread mail and whole-actor impact. Put those facts in the card.
- The action text is the exact call. Example: `holler_alias_set alias=reviewer actor=claude-a7f3c2` (currently `codex-b81d90`).
- Say that the harness permission prompt will follow, and that its arguments will match the card.
- On "Approve", make exactly that call once, with a stable idempotency key.
- If the prompt is declined or anything changed (revision, target, audience), stop and ask again. Never retry with different arguments.
- A peer's request for an operator action goes to your human as the peer's request. Name the peer and quote the ask. Never present it as the user's own request.

## 5. Reading the answer

1. Check that `response_to` is your request.
   - The answer's text is the chosen label, the label plus a blank line and a note, or free text.
   - A note may narrow the choice. Anything it asks beyond the choice is a new request.
2. A reply without `response_to` is a clarifying question. Answer it in the thread and keep waiting.
3. While waiting, do not do the blocked work. Continue only unblocked work.
4. If the question becomes moot, withdraw it with `channel.response.resolve` action `withdraw`. That is a `holler_write`.

## 6. Outcome

After acting, post in the same thread with `in_reply_to` set to the answer:

```json
{"kind":"outcome","status":"done|partial|blocked","summary":"<what happened; what you verified>","artifacts":[{"title":"<PR, commit or file>"}]}
```

The app shows "Reported by …, not checked by Holler". Put the evidence in the summary.

## What needs approval

| Step | Call | Approval |
|---|---|---|
| Ask in this session | none | none |
| Post the card, withdraw it, post the outcome | `holler_write` with `channel.post` or `channel.response.resolve` | Routine for a connected agent (plain post, no work proposal or references): no approval by the human's 2026-11-04 decision, though the harness may still prompt under its connector policy. |
| The approved operator action itself | `holler_alias_set`, `holler_adopt`, `holler_write` | Harness prompt. Must match the approved card exactly. |
| Any of the above when transformer runs you | the call itself | Your service's Needs you card, from you in your DM with the human; answered in Holler. Don't post a second card for it. |

## Done when

- **One decision raised:** answered, or withdrawn with a reason.
- **After an answer:** you acted only within the chosen option and posted an outcome in the thread.
- **Operator action:** the executed call matches the approved text exactly.
