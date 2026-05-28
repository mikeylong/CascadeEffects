# Therac-25 Short Beat And Shot Plan

## Short Plan

- `episode_id`: `therac-25`
- `short_id`: `therac_short_minimal_surreal_v1`
- `short_script_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/therac_short_minimal_surreal_v1.txt`
- `target_audio_path`: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_minimal_surreal_v1/final/therac_short_minimal_surreal_v1.wav`
- `target_transcript_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_minimal_surreal_v1/transcripts_mastered/therac_short_minimal_surreal_v1.diarized.txt`
- `staging_model`: `eleven spoken transcript cues staged as seven visual segments`

## Beats

### `beat_01_denial_initial`

- `cue_range`: `00:00:00.031-00:00:08.682`
- `target_duration_seconds`: `8.702`
- `archetype`: `room_or_interior`
- `primary_subject`: `quiet Therac treatment room with the machine and covered patient relationship immediately readable`
- `anomaly_carrier`: `the machine remains calm while the clinical relationship is already unsafe`
- `still_strategy`: `use keep still therac_25__patient_vs_machine_pass_02`
- `motion_strategy`: `current proof uses a still hold; open motion only if the opening timing and denial beat are approved`
- `notes`: `covers the overdose claim and the "then it happened again" turn`

### `beat_02_interlocks_removed`

- `cue_range`: `00:00:08.702-00:00:13.769`
- `target_duration_seconds`: `6.028`
- `archetype`: `single_object_or_device`
- `primary_subject`: `Therac machine head and hidden state mismatch`
- `anomaly_carrier`: `a missing independent physical safety layer implied by the unsafe internal state`
- `still_strategy`: `use keep still therac_25__hidden_state_mismatch_redesign_pass_02`
- `motion_strategy`: `current proof uses a still hold; future motion should keep the machine canonical and avoid diagram/UI text`
- `notes`: `anchors the script line about physical interlocks being replaced with software checks`

### `beat_03_race_condition_wrong_state`

- `cue_range`: `00:00:14.730-00:00:23.321`
- `target_duration_seconds`: `9.044`
- `archetype`: `single_object_or_device`
- `primary_subject`: `software-trust machine state carried through the treatment hardware`
- `anomaly_carrier`: `small state mismatch becoming a full-power unfiltered beam condition`
- `still_strategy`: `use source still from keep motion case therac_25__software_trusted_itself_pass_02`
- `motion_strategy`: `import keep motion clip therac_25__software_trusted_itself_pass_02; normalized proof pads the final frame to cover the full spoken beat`
- `notes`: `motion reads well at the start; freeze-tail should be reviewed for acceptability`

### `beat_04_reused_code`

- `cue_range`: `00:00:23.774-00:00:32.185`
- `target_duration_seconds`: `9.694`
- `archetype`: `single_object_or_device`
- `primary_subject`: `machine-over-patient trust chain`
- `anomaly_carrier`: `reused code treated as proven safety`
- `still_strategy`: `use keep still therac_25__trust_chain_machine_over_patient_pass_02`
- `motion_strategy`: `current proof uses a still hold; future motion should stay locked and institutional rather than becoming a software animation`
- `notes`: `keeps the reused-code line in the same systems-trust visual family as the closing safety-layer beat`

### `beat_05_reports_denial`

- `cue_range`: `00:00:33.468-00:00:42.962`
- `target_duration_seconds`: `10.815`
- `archetype`: `single_human_figure`
- `primary_subject`: `clinical operator at the Therac console`
- `anomaly_carrier`: `reported errors absorbed into routine workflow`
- `still_strategy`: `use source still from keep motion case therac_25__operator_white_coat_cleanup`
- `motion_strategy`: `import keep motion clip therac_25__operator_white_coat_cleanup; normalized proof pads the final frame to cover the full reports-denial passage`
- `notes`: `human-facing beat covers operators, manufacturer denial, and the pattern becoming real`

### `beat_06_no_safety_layer`

- `cue_range`: `00:00:44.283-00:00:56.246`
- `target_duration_seconds`: `13.107`
- `archetype`: `single_object_or_device`
- `primary_subject`: `Therac machine trust chain over the patient`
- `anomaly_carrier`: `no independent safety layer between software error and patient harm`
- `still_strategy`: `use keep still therac_25__trust_chain_machine_over_patient_pass_02`
- `motion_strategy`: `current proof uses a still hold; future motion should be slow, locked, and protective-layer focused`
- `notes`: `main systemic thesis beat before the final consequence line`

### `beat_07_final_consequence`

- `cue_range`: `00:00:57.390-00:01:00.976`
- `target_duration_seconds`: `3.585601`
- `archetype`: `single_object_or_device`
- `primary_subject`: `software-trust machine state returns as the final visual thesis`
- `anomaly_carrier`: `small cause producing massive consequence`
- `still_strategy`: `use source still from keep motion case therac_25__software_trusted_itself_pass_02`
- `motion_strategy`: `import and trim keep motion clip therac_25__software_trusted_itself_pass_02 to the final line`
- `notes`: `the corrected ending lands as a complete sentence over promoted motion`
