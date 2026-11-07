# Evidence rules

- Never invent numbers, customers, quotes or reviews.
- Every number carries a source, a date and a label (measured, user-provided, calculated, estimated, proxy). Missing evidence is `[NEED: …]`.
- Numbers quoted in skills or templates are illustrations; they need a primary source before anyone uses them publicly.
- Keep observed and estimated apart. Correlation is not causation. Before the decision date or the minimum sample, a number is noise, not a win.
- All copy is a draft (`Status: DRAFT`) until the human approves it.

## Pre-registration

- Before a change meant to move a metric ships, register it with experiment-card: the metric and its authoritative source, a dated baseline, the target, the decision date, the minimum sample, the kill criterion and the predicted outcome.
- `.agents/experiments.jsonl` is append-only and written only by the experiment-card script. A changed target is a new card that supersedes the old one.
- At the decision date, read out with the script and report misses as misses.
