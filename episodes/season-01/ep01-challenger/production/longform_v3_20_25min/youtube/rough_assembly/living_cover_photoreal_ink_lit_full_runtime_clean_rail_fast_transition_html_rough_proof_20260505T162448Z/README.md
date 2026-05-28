# Challenger Living Cover Full-Runtime Clean Rail Fast-Transition HTML Rough Proof

Packet: `living_cover_photoreal_ink_lit_full_runtime_clean_rail_fast_transition_html_rough_proof_20260505T162448Z`
Status: `review_ready_pending_human_clean_rail_fast_transition_html_rough_keep`
Human disposition: `defer`
Full runtime: `00:21:29.131`
MP4 render created: `false`
Final assembly in scope: `false`
YouTube action in scope: `false`

This packet tightens the current full-runtime YouTube-legibility MP4 proof. The stale MP4 is recorded as `tighten` because it baked in two progress bars, added gradient/vignette treatment, and held chapter transitions long enough to reveal jitter.

The new artifact is HTML-only. It removes the top-right and bottom progress bars, removes the global gradient/vignette layer, keeps the rail/card treatment flat for legibility, and caps section typography/visual transitions at roughly `600ms`.

## Review Artifact

- Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_clean_rail_fast_transition_html_rough_proof_20260505T162448Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_clean_rail_fast_transition_html_rough_proof_20260505T162448Z/rough_assembly_manifest.json`
- Review packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_clean_rail_fast_transition_html_rough_proof_20260505T162448Z/review/rough_assembly_review_packet.md`

## Full-Runtime Structure

The right rail still uses 8 major sections for the full approved audio. The active section expands into a video-first box: title, one short summary, and one dominant current subbeat with optional adjacent subbeats only when they remain legible. The visible rail does not show top timecode.

- 1. First Warning
- 2. Cold Joint
- 3. Joint Problem
- 4. Warning Becomes Process
- 5. Processed Warning
- 6. Launch-Night Decision
- 7. Recommendation Reversal
- 8. Routine Pressure

## Source Chain

- Source art: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png`
- Approved audio: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/recording_20260501_v3_20_25min/challenger_longform_v3_20_25min_recording_review.wav`
- Full captions: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/transcript_source/challenger_longform_v3_20_25min_recording_review.diarized.vtt`
- Full transcript timing: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/transcript_source/challenger_longform_v3_20_25min_recording_review.diarized.srt`

Audio, captions, and transcript are referenced in place. They were not copied, regenerated, or modified.

## Legibility Controls

- Active title remains roughly the prior scale.
- Active summary text target: `22px` at 1080p.
- Active current-subbeat target: `25px` at 1080p.
- Tiny preview sizes hide small subtext rather than showing unreadable/dithered copy.
- QA includes 1920x1080, 1280x720, 320x180, and 168x94 screenshots plus a computed-style legibility audit.

## Clean Rail Controls

- Baked progress UI: `removed`
- Top-right rail progress: `removed`
- Bottom progress bar: `removed`
- Global gradient/vignette layer: `removed`
- Transition crossover: `600ms`
- Smoothstep window: `0.3s` before and after each section boundary

## Locked Actions

No MP4/MOV render, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.

## Staged Rail Transition Tighten Record

Human disposition: `tighten`

Reviewer note: the transition still feels jumpy or rough because too many layout, typography, detail, and source-art changes happen at once.

Required changes:

- Keep total chapter crossover near `600ms`.
- Stage outgoing detail, new title/accent, and new summary/current subbeat as separate phases.
- Remove animated layout reflow for font size, max height, display, and active-card padding.
- Use stable rail slots with a constant-size active detail layer.
- Delay source-art drift until after the outgoing-detail settle phase.

Superseding HTML-only review artifact: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_staged_rail_transition_html_rough_proof_20260505T164049Z`
