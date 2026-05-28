# Therac-25 Short Production Pilot

## Short

- `episode_id`: `therac-25`
- `short_id`: `therac_short_minimal_surreal_v1`
- `short_script_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/therac_short_minimal_surreal_v1.txt`
- `short_manifest_path`: `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_minimal_surreal_v1.json`
- `governing_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md`
- `audio_skill_path`: `/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md`
- `style_skill_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/SKILL.md`
- `promotion_workflow_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/judgment/promotion_workflow.md`
- `keeper_registry_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/judgment/keeper_registry.md`
- `proof_review_template_path`: `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`

## Audio State

- `short_audio_pipeline_dir`: `/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_minimal_surreal_v1`
- `short_audio_package_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_minimal_surreal_v1/audio_package.json`
- `short_audio_wav_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/final/therac_short_minimal_surreal_v1.wav`
- `short_audio_transcript_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_minimal_surreal_v1/transcripts_mastered/therac_short_minimal_surreal_v1.diarized.txt`
- `short_audio_review_disposition`: `keep`

## Current Keeper Inventory

- `keeper_still_total`: `3 still keepers used as still-hold coverage`
- `keeper_motion_total`: `2 motion keepers used as imported motion coverage`
- `keeper_short_total`: `0 promoted keeper shorts; 1 mixed-review motion proof ready for timing review`

## Approved Motion Keepers

- `case_id`: `therac_25__software_trusted_itself_pass_02`
- `artifact_path`: `/Users/mike/AI/outputs/mlx-video/20260411T054350Z-7d886bea-comfy-therac_25__software_trusted_itself_pass_02__minimal_surreal_editorial_v3_00001_-i2v-20260411T054350Z.mp4`
- `role_in_short`: `beats 03 and 07; beat 03 pads the final frame after the 5.04s motion source, while beat 07 trims the keeper clip to the final thesis line`

- `case_id`: `therac_25__operator_white_coat_cleanup`
- `artifact_path`: `/Users/mike/AI/outputs/mlx-video/20260410T230813Z-765bd40b-comfy-therac_25__operator_white_coat_cleanup__minimal_surreal_editorial_v3_00001_-i2v-20260410T230828Z.mp4`
- `role_in_short`: `beat 05 reports-denial section; the clip carries the operator routine and pads its final frame to cover the full spoken beat`

## Approved Still Keepers

- `case_id`: `therac_25__patient_vs_machine_pass_02`
- `artifact_path`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_01_patient_vs_machine_pass_02/20260411T054650Z/therac_25__patient_vs_machine_pass_02/minimal_surreal_editorial_v3/therac_25__patient_vs_machine_pass_02__minimal_surreal_editorial_v3_00001_.png`
- `role_in_short`: `beat 01 opening denial and repeated-overdose setup`

- `case_id`: `therac_25__hidden_state_mismatch_redesign_pass_02`
- `artifact_path`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_04_hidden_state_mismatch_redesign_pass_02/20260411T054555Z/therac_25__hidden_state_mismatch_redesign_pass_02/minimal_surreal_editorial_v3/therac_25__hidden_state_mismatch_redesign_pass_02__minimal_surreal_editorial_v3_00001_.png`
- `role_in_short`: `beat 02 physical interlocks replaced by software checks`

- `case_id`: `therac_25__trust_chain_machine_over_patient_pass_02`
- `artifact_path`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_07_trust_chain_machine_over_patient_pass_02/20260411T054555Z/therac_25__trust_chain_machine_over_patient_pass_02/minimal_surreal_editorial_v3/therac_25__trust_chain_machine_over_patient_pass_02__minimal_surreal_editorial_v3_00001_.png`
- `role_in_short`: `beats 04 and 06; reused-code trust chain and missing independent safety layer`

## Current Compiled Short

- `compiled_short_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.mp4`
- `compiled_short_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.json`
- `compiled_short_beat_sheet_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__beat_sheet.png`
- `compiled_short_note_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/production/short_cut_review.md`
- `compiled_short_disposition`: `diagnostic only; mixed review short; rebuilt against clean-script 60.975601s VO`

## Deferred Gaps

- `beat_id`: `beat_01_denial_initial`, `beat_02_interlocks_removed`, `beat_04_reused_code`, `beat_06_no_safety_layer`
- `carrier`: `still-hold coverage from keep stills`
- `failure_mode`: `visual timing is covered, but these beats are not promoted motion clips`
- `next_carrier`: `if the proof timing works, open beat-local motion passes from the current keep stills`

- `beat_id`: `beat_03_race_condition_wrong_state`, `beat_05_reports_denial`
- `carrier`: `5.04s keep motion clips normalized to longer spoken beats`
- `failure_mode`: `motion starts cleanly but freezes at the tail because the approved source clips are shorter than the spoken beat`
- `next_carrier`: `either split the spoken beat into shorter visual segments or generate longer beat-local motion from the same keeper stills`

## Next Production Queue

1. `review`: `watch the compiled proof for pacing, visual order, and whether the new final line lands cleanly`
2. `beat_01_denial_initial`, `beat_02_interlocks_removed`, `beat_04_reused_code`, `beat_06_no_safety_layer`: `open motion only after timing and shot order are accepted`
3. `beat_03_race_condition_wrong_state`, `beat_05_reports_denial`: `decide whether the freeze-tail is acceptable for proof review or whether each needs a longer motion pass`

## Blocking Gap

- `next_blocking_gap`: `user review of the mixed proof before spending new motion passes`
