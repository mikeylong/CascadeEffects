# Critique Integration Note: Air France Flight 447

status: pass
gate: critique_integration
episode_id: ep11-air-france-447
pre_integration_script_sha256: c59d479aae3c50a364db1909dfde3f3ad3860f5a01e13e1e49bc8c46ab717a95
post_integration_script_sha256: eb10ed79b19eb3fcbb8b89f292ef4c2436bf0dd774b97300d1f1d62e2533d03e

## Required Changes Integrated

1. The automation-mode primer now states that unreliable airspeed changes the working contract, not just the instrument reading.
2. The handoff chapter now clarifies that angle of attack is visible in flight-data reconstruction but was not a simple crew-facing number that named the condition.
3. The closing shorthand now says the familiar story is that AF447 `ended in a stall`, preserving the stall fact without making it the whole explanation.

## Changes Deferred

- Legal-status context remains excluded. Mike approved the CVR/source guardrails and did not ask for a legal end note. The BEA technical mechanism remains the episode center.
- No cockpit-dialogue excerpts were added. The script already uses CVR/FDR as sequence support, and adding transcript lines would increase the risk of transcript-driven psychology without improving the mechanism.

## Remaining Blocker

Mike/human script approval for audio is still pending. Audio render remains unauthorized until the exact post-integration script revision receives explicit human approval.
