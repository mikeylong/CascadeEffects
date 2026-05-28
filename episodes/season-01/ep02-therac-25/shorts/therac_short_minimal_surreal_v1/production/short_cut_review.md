# Therac-25 Short Cut Review

## Short Cut Review

- `episode_id`: `therac-25`
- `short_id`: `therac_short_minimal_surreal_v1`
- `compiled_short_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.mp4`
- `compiled_short_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.json`
- `compiled_short_beat_sheet_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__beat_sheet.png`
- `short_audio_wav_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/final/therac_short_minimal_surreal_v1.wav`
- `short_audio_transcript_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_minimal_surreal_v1/transcripts_mastered/therac_short_minimal_surreal_v1.diarized.txt`
- `review_type`: `reel`
- `gate_level`: `reel`
- `reel_class`: `mixed review short`
- `disposition`: `diagnostic only`
- `failure_reason`: `the proof covers the clean-script 60.975601s voiceover with approved Therac source assets, but beats 01, 02, 04, and 06 are still holds, and beats 03 and 05 pad the tail of shorter keep motion clips; this is a timing and order proof, not a fully promoted keeper short`
- `next_action`: `review the MP4 for pacing, shot order, and whether the clean-script read fixes the unnatural inflection issue; if approved, open motion only on the still-held lanes and decide whether beats 03 and 05 need longer motion coverage`

## Coverage Check

- `opening_covered`: `true`
- `middle_covered`: `true`
- `closing_covered`: `true`
- `all_included_assets_are_keep`: `false`

## Included Assets

- `clip_case_id`: `therac_short_minimal_surreal_v1_motion_proof_20260417T040035Z`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.mp4`
- `clip_note`: `mixed-review motion proof built from the clean-script ElevenLabs WAV, four still-held keeper stills, and two imported motion keepers`

- `clip_case_id`: `beat_01_denial_initial_still_hold`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_01_denial_initial__normalized.mp4`
- `clip_note`: `still hold from keep still therac_25__patient_vs_machine_pass_02`

- `clip_case_id`: `beat_02_interlocks_removed_still_hold`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_02_interlocks_removed__normalized.mp4`
- `clip_note`: `still hold from keep still therac_25__hidden_state_mismatch_redesign_pass_02`

- `clip_case_id`: `beat_03_race_condition_wrong_state_motion_import`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_03_race_condition_wrong_state__normalized.mp4`
- `clip_note`: `imported keep motion therac_25__software_trusted_itself_pass_02, padded to cover the full spoken beat`

- `clip_case_id`: `beat_04_reused_code_still_hold`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_04_reused_code__normalized.mp4`
- `clip_note`: `still hold from keep still therac_25__trust_chain_machine_over_patient_pass_02`

- `clip_case_id`: `beat_05_reports_denial_motion_import`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_05_reports_denial__normalized.mp4`
- `clip_note`: `imported keep motion therac_25__operator_white_coat_cleanup, padded to cover the full reports-denial passage`

- `clip_case_id`: `beat_06_no_safety_layer_still_hold`
- `clip_disposition`: `diagnostic only`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_06_no_safety_layer__normalized.mp4`
- `clip_note`: `still hold from keep still therac_25__trust_chain_machine_over_patient_pass_02`

- `clip_case_id`: `beat_07_final_consequence_motion_import`
- `clip_disposition`: `keep`
- `clip_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/clips/normalized/beat_07_final_consequence__normalized.mp4`
- `clip_note`: `trimmed keep motion therac_25__software_trusted_itself_pass_02 under the corrected final line`

## Deferred Gaps Carrying Forward

- `beat_id`: `beat_01_denial_initial`, `beat_02_interlocks_removed`, `beat_04_reused_code`, `beat_06_no_safety_layer`
- `carrier`: `still-hold keeper stills`
- `failure_mode`: `not promoted motion`
- `next_carrier`: `open beat-local motion after timing approval`

- `beat_id`: `beat_03_race_condition_wrong_state`, `beat_05_reports_denial`
- `carrier`: `imported keep motion clips with padded tails`
- `failure_mode`: `source clips are shorter than the spoken beat`
- `next_carrier`: `split or rerender longer motion if the freeze-tail distracts`
