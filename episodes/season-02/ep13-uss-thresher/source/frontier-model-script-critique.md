# Frontier Model Script Critique: USS Thresher

status: pass
gate: frontier_model_script_critique
episode_id: ep13-uss-thresher
created_at: 2026-05-29T00:37:46Z

## Script Reviewed

- Path: `episodes/season-02/ep13-uss-thresher/source/longform-script.md`
- SHA-256 reviewed: `940e41554c70e1f782eed96f64e014a7312aedd956d8fa90c97a4f4f0673e84d`

## Critic Identity

Claude is the default critic for this gate, but it was not available in the current tool context.

Substitution rationale: User requested spawned Codex agents; Claude tool unavailable in current tool context; critique performed by Codex subagent using inherited frontier GPT-5-class model.

## Verdict

Pass after required integration edits.

The script reads the source audit and writer packet closely, preserves Mike's approved direction, and keeps the episode on the changed-first frame: test depth changed the recovery envelope before the outside system could fully interpret the casualty. It introduces SUBSAFE near the beginning as the institutional answer rather than a closing footnote, keeps the mechanism strong without pretending the initiating cause is proven, and avoids turning the loss into a clean courtroom reenactment.

The script does not authorize audio. It still needs Mike/human script approval for audio after this critique and integration record.

## Required Changes

1. Tighten one over-dramatic margin sentence. The draft said Thresher made the system fit visible by "destroying the margin." The integrated revision keeps the same claim but makes it more precise and less rhetorical.
2. Make the flooding/brazed-joint wording unmistakably conditional. The draft already used "probable or postulated," but the sentence needed one more caution marker before pointing to a vulnerable piping or brazed-joint path.
3. Reduce the repeated "deep ocean does not care" cadence in Chapter 4. The passage was narratable, but it leaned toward aphorism. The integrated revision keeps the depth-pressure claim and improves the Mike-style rhythm.

## Optional Changes

- A later fact-check pass can stage exact Court of Inquiry, NAVSEA, or NASA safety-message wording before audio approval if Mike wants more primary-source texture.
- The final communications can stay fragmentary in the current script. Do not add dramatic dialogue unless a later source pass quotes and contextualizes the exact record.
- Visual planning should keep Mike's preference for familiar submarine/underwater objects and avoid split-screen framing, but those notes do not need to become narration.

## Source And Factual Cautions

- Do not state a single initiating cause as proven.
- Treat flooding, brazed-joint failure, and the exact casualty sequence as probable, postulated, or disputed unless a primary source supports stronger language.
- Present final communications as partial and garbled evidence, not as a clean scene.
- Keep SUBSAFE as the major institutional consequence and boundary-control answer.
- Avoid overclaiming what Skylark, shore-side observers, or rescue systems could have known or changed in real time.

## Style And Doctrine Notes

- The script is aligned with Cascade Effects doctrine: the headline is familiar, but the episode shows the mechanism underneath it.
- The strongest mechanism is the shrinking recovery envelope under test conditions, not a single failed part.
- The title direction, `USS Thresher and the Boundary No One Could Cross Back From`, is preserved.
- The tone is calm, evidence-first, and restrained enough for a 12-18 minute compact long-form episode.

## Audio-Gate Blockers

- `frontier_model_script_critique_read`: pass after this packet.
- `critique_integration_read`: pass after the integration note and post-edit hash are recorded.
- `human_script_approval_for_audio_read`: pending.
- `audio_render_authorized`: false.

Audio must remain blocked until Mike/human approval is recorded for the exact post-integration script revision.
