# Frontier-Model Script Critique: Air France Flight 447

status: pass
gate: frontier_model_critique
episode_id: ep11-air-france-447
script_reviewed: episodes/season-02/ep11-air-france-447/source/longform-script.md
script_sha256_reviewed: c59d479aae3c50a364db1909dfde3f3ad3860f5a01e13e1e49bc8c46ab717a95

## Critic Identity

Critic: Codex subagent using inherited frontier GPT-5-class model.

Substitution rationale: User requested spawned Codex agents; Claude tool unavailable in current tool context; critique performed by Codex subagent using inherited frontier GPT-5-class model.

## Verdict

Pass after targeted integration.

The draft is aligned with Mike's approved writer-packet direction. It preserves the `Air France 447: What the System Hid` title, includes a short automation-mode primer, and keeps CVR material at the evidence/context level instead of using cockpit dialogue as drama or character judgment.

The script answers the Cascade Effects spine: what changed, why the change was hard to recognize, and how delayed recognition became consequence. It avoids a pilot-error recap and keeps the mechanism centered on unreliable airspeed, automation handoff, degraded cues, workload, training expectations, and delayed stall recognition.

## Required Changes

1. Make the automation-mode primer more explicit about why unreliable airspeed changes the working contract rather than only creating a bad instrument reading.
2. Clarify that angle of attack is useful in flight-data reconstruction but was not a simple crew-facing cue that named the stall for the cockpit.
3. Soften the closing shorthand from `Air France 447 stalled` to wording that makes the stall the final aerodynamic state, not the whole explanation.

## Optional Changes

- A later human review could decide whether to add a short legal-status end note. The current script should leave it out unless Mike asks for it because legal context is separate from the BEA technical finding.
- If the visual plan later uses FDR parameter graphics, the narration can stay as written; any visual callout should carry the angle-of-attack caveat from the integrated draft.

## Source / Factual Cautions

- Do not imply weather alone caused the accident.
- Do not imply the pilots had a clean, simple angle-of-attack display that would have named the stall.
- Do not present CVR transcript material as character psychology or cockpit theater.
- Do not overstate interface-design claims beyond the local source audit, writer packet, and BEA-grounded source base.
- Keep legal context separate from BEA safety findings unless Mike explicitly asks for a short end note.

## Style / Doctrine Notes

- The draft is in the right lane for Cascade Effects: changed-first, mechanism-led, evidence-first.
- The strongest repeatable line is the system-contract framing. Use it sparingly; the episode should not become an abstract automation essay.
- The automation-mode primer is necessary and should stay short.
- The closing works because it lands on shared legibility, not villainy or spectacle.

## Audio-Gate Blockers

Audio is not authorized.

Remaining blocker: Mike/human script approval for audio has not been recorded for the post-integration script revision. The frontier critique and integration can pass, but `human_script_approval_for_audio_read` must remain `pending` and `audio_render_authorized` must remain `false`.
