# Challenger Continuous Ambient End-Screen Review Packet

Created: `20260515T064720Z`
Predecessor: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z`

## Change

This proof preserves the current script-locked caption packet and replaces only the end-screen clocking behavior. The story clock remains clamped at `1214.763537s` for rail state, chapter text, visual framing, and caption suppression. The ambient clock continues through the full runtime for the Living Cover aircraft, dust, beacon, and practical-light animation.

## Review Reads

- `continuous_living_cover_ambient_read`: pass: ambient clock and canvas hash differ between end-screen safe-window samples.
- `youtube_target_geometry_static_read`: pass: video target boxes, subscribe target, title raster, and safe-zone geometry are stable.
- `caption_suppression_read`: pass: captions are blank at and after outro start.
- `rail_fade_read`: pass: rail fade/suppression is unchanged.
- Script-locked caption reads are inherited from the predecessor and must remain passing.

## Browser QA

- `continuous_ambient_end_screen_browser_qa_20260515T065157Z.json` passes page load, fixed 1920x1080, story clock clamp, continuous ambient motion, static YouTube target geometry, caption suppression, and rail fade.
- Ambient canvas hashes differ between `1225.553197s` (`ba5fa933`) and `1242.0s` (`658c12bf`), while target geometry remains stable.

Public upload remains out of scope. Render QA should compare static overlay geometry, not identical whole-frame pixels, because the background is expected to move.

# Challenger Script-Locked Caption Review

Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/player.html`

Local review URL: `http://127.0.0.1:8818/player.html`

Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/rough_assembly_manifest.json`

## What Changed

- Replaced only caption assets and caption references.
- Caption text source is the locked narration script.
- Caption timing source is the timed corrected VTT, used only for timing.
- Audio, visuals, chapters, matte, dust, aircraft, intro music fade, outro, and transparent end-screen overlay behavior are unchanged.
- No MP4 was rendered.

## QA Reads

- caption_text_matches_script_read: `pass`
- caption_alignment_coverage_read: `pass_0.987134`
- caption_asr_text_not_used_read: `pass`
- caption_no_caption_after_outro_start_read: `pass`
- caption_rail_safe_chunk_read: `pass`
- known_regression_fixture_read: `pass_too_weak_not_two_weeks`

QA file: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/qa/captions/script_locked_caption_qa.json`

Regression fixture: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/qa/captions/challenger_too_weak_regression_fixture.json`

## Review Focus

- Confirm the rail captions now read as the narration script rather than ASR text.
- Around `00:01:22.554`, confirm the caption says `too weak`, not `two weeks`.
- Confirm caption placement, rail fit, playback, and outro suppression still behave like the predecessor.

Please review the HTML proof and reply with exactly one disposition: `keep`, `tighten`, or `reject`.
