# Frontier-Model Script Critique: Tenerife

status: pass
episode_id: ep12-tenerife
gate: frontier_model_critique
script_reviewed: episodes/season-02/ep12-tenerife/source/longform-script.md
script_sha256_reviewed: 7d02a3eb4f77e0c12b1f52159165493ed9d470463d81e2a62dfd0ff17b5b6332
critic_model_tool: Codex subagent using inherited frontier GPT-5-class model
substitution_rationale: User requested spawned Codex agents; Claude tool unavailable in current tool context; critique performed by Codex subagent using inherited frontier GPT-5-class model.

## Verdict

Pass after required integration.

The script reads the actual longform draft and carries Mike's direction: `Tenerife: One Runway, Two Realities`, the mechanism that shared runway reality failed under radio ambiguity, system analysis instead of courtroom reenactment, and a full CRM closing beat. It keeps the official direct cause visible while giving the episode a Cascade Effects mechanism rather than a captain-villain frame.

The draft was not audio-authorized at review time. Required changes below had to be integrated before the critique could pass.

## Required Changes

1. Replace the one place where the draft risked sounding like a personality judgment. The script should reject captain-villain framing without calling the KLM captain arrogant as narration.
2. Tighten the clearance distinction. The episode depends on the difference between ATC route clearance, takeoff clearance, runway occupancy, and the tower's intended state. The draft needed to state that KLM received an ATC route clearance, not a takeoff clearance.
3. Replace generic `runway clearance` phrasing with `takeoff clearance` where the safety artifact is being described.
4. Keep the CRM close, but make it about challenge, command responsibility, and unresolved safety information. Do not let it become a broad motivational claim about crews being nicer to each other.
5. Preserve the final audio blocker: human approval remains pending, and no audio render can be authorized from this critique alone.

## Optional Changes

- A later human rhythm pass can reduce a few repeated `It became...` and `It showed...` structures if Mike wants a less beat-driven narration. This is stylistic and not a gate blocker.
- Exact CVR quotations should remain out of the script unless the next fact pass verifies them against the official report or FAA Lessons Learned page. The current draft mostly paraphrases, which is appropriate for this stage.

## Source And Factual Cautions

- Anchor the direct cause in the Spanish findings excerpt: KLM took off without clearance, did not obey the stand-by instruction, did not interrupt takeoff after Pan Am reported runway occupancy, and the captain answered the flight engineer's runway-clear query affirmatively.
- Keep contributing factors in their lane. The official findings treat weather, simultaneous transmissions, inadequate language, Pan Am not leaving at the third intersection, and unusual congestion as contributors. The Las Palmas bomb incident and KLM refueling should not be treated as direct factors.
- The FAA Lessons Learned page supports the route-clearance versus takeoff-clearance distinction, the runway backtracking/congestion setup, the Pan Am C-3/C-4 caution, and CRM/authority-gradient discussion.
- Do not claim Tenerife single-handedly created modern CRM. The script can say the accident belongs in the history of why aviation treated cockpit challenge and phraseology more seriously.
- Keep Pan Am registration as `N736PA` if registration appears in narration or source notes.

## Style And Doctrine Notes

- The script follows Cascade Effects doctrine: changed-first framing, mechanism-led narration, evidence separated from interpretation, and no generic disaster recap.
- The strongest narrative line is physical: one runway became both taxi route and departure path, then visibility and radio ambiguity split the shared operational picture.
- The CRM section works because it treats the cockpit as a system layer, not a private drama.

## Audio-Gate Blockers

- Human/Mike script approval for audio remains pending.
- Audio render remains unauthorized until `human_script_approval_for_audio_read` is `pass` for the exact post-integration script revision.
