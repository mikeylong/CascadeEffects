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
