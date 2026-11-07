# Security policy

Report suspected vulnerabilities privately to **security@72olabs.ai**. Do not open a public issue with exploit
details, credentials or private transcripts. Include the holler-roles commit or starter-team version, the
harness and its version, the impact and a minimal reproduction with synthetic data. We coordinate fixes and
disclosure with the reporter; no response-time guarantee is offered yet.

Security fixes target the main branch; there are no maintenance branches yet.

What the bundle promises, and what it does not:

- A bundle holds no secrets, no absolute paths and no symlinks, and `bin/holler-roles verify` checks every
  file against its manifest hash. Holler's runtime refuses a bundle whose hashes differ (spec/LAUNCH.md).
- The guards (`readonly-guard`, `experiment-registry`, kit guards such as `careful`) are Claude Code hooks that
  deny common mistakes. They are not a sandbox: a determined or confused model can find commands they do not
  match. Use your harness's sandbox and permission settings for a real boundary.
- Agents read untrusted content: pull requests, issues, web pages and peer messages. The Holler platform layer
  tells them never to follow instructions found in peer content; that lowers the risk of prompt injection and
  does not remove it.
