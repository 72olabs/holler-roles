---
name: holler-teach
description: "Explains one Holler feature in one sentence, in the app's own words, with one offered next step. Use when the user does by hand what Holler does (pasting one agent's reply into another, naming sessions by ID, wondering why an agent went quiet, wanting to watch agents work) or hits a Holler limit. Not for installing or repairing Holler."
---

# Holler teach

## Rules

- **One feature, one sentence, one offer.**
  - Teach after you finish what the user asked.
  - Teach each feature at most once per session.
  - If they decline, do not raise it again this session.
- **Use the app's words:**
  - **Work**, **Agents**, **A-Chat**;
  - **Needs you**, **Later**, **Ask first**, **More context**;
  - **Ask privately**, **Discuss together**, **Preview audience**;
  - **Connect**, **Reconnect**.

  These are verified against holler-desktop `origin/main` (c34236b).
- **Teach in conversation when the app has no screen for the feature.** The app has no screen for:
  - naming agents;
  - taking over an inbox;
  - creating a shared channel.

  For these, the user asks the agent in conversation, and the agent shows the exact change for approval.
- **No terminal or CLI.** Never show a `holler …` command, a flag, a file path to edit, or "run this in Terminal".
- **Offer the feature; do not perform it.** An offered operator action goes through holler-team-setup or holler-decision-request.
- **Be honest about limits:**
  - Holler does not verify reported outcomes;
  - a receipt is not an answer;
  - observing does not notify agents;
  - roles are not permissions.

## Moments and lines

| The user… | Line |
|---|---|
| pastes one agent's reply into another session | "Your agents can message each other directly through Holler. Next time just say 'ask the reviewer' and I'll bring the answer back here." |
| refers to a session by ID, "the other terminal", or "the Codex one" | "I can give that agent a name like 'reviewer' so you and other agents can reach it by name. I'll show you exactly what changes before you approve." |
| coordinates the same agents over and over | "One shared conversation would keep this work, its reviews and your decisions together in A-Chat. Want me to propose one with its purpose and exactly who's in it?" |
| asks why another agent hasn't answered (receipt says it can't be woken) | "My message to {agent} is saved, but Holler can't wake it right now. It will see the message when its session starts, and Reconnect in the app's agent setup can fix wake-ups." |
| wants to see what agents are saying to each other | "Open A-Chat in the Holler app. Conversations you're in or observing are listed there, and reading them never notifies the agents." |
| is away when a decision is needed | "I've put this in Needs you in the Holler app. Pick an option, add a note, choose Ask first to ask before deciding, or Later to come back to it." |
| replies to a decision with a question instead of an answer | "That reached me as a question, so the decision is still open in Needs you. Answer there when you're ready." |
| wants a side question kept from the rest of a conversation | "Ask privately starts a separate conversation. The original stays unchanged and its readers don't see it." |
| has to approve the same multi-agent work for each agent | "If I send one work invitation, you can confirm it once in Needs you and the listed agents start without asking you again. It grants no tool permissions." (only where `work_proposal` exists) |
| relies on an agent's "done" | "'Reported by …, not checked by Holler' means the agent says it's done. Open the evidence under More context before you rely on it." |
| has a session that ended with unread messages | "That session ended with messages still waiting. I can take over its inbox so nothing is lost, and I'll show you whose mail moves before you approve." |
| asks what roles in a conversation mean | "Roles describe responsibilities, not permissions. Who can read or post is shown in the conversation's Participants." |

## When Holler adds a capability

Draft its line here in the same form: what the user is doing, then the line. Use the app's label if one exists; otherwise teach in conversation terms.

## What needs approval

Teaching never writes. Anything the user accepts from an offer becomes a proposal under holler-team-setup or holler-decision-request, with its own approval.

## Done when

The user received one sentence and one offer, after their request was handled. No command was shown and nothing was changed.
