# Challenger Local Motion Quality Experiment Pass 01

- `review_date`: `2026-04-14`
- `experiment_id`: `local_motion_quality_challenger_phase1`
- `run_root`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T211440Z`
- `short_manifest_path`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_minimal_surreal_v3_trimmed.json`
- `scope`: `current MLX/LTX lane only`
- `result`: `keep baseline`
- `phase_2_status`: `required`

## Experiment Decision

- `control_clip`: `beat_02a`
- `stress_clip`: `beat_01b`
- `baseline_result`: `completed`
- `candidate_dev_result`: `runtime gate failure before completion`
- `candidate_dev_two_stage_hq_result`: `not run after dev control lane exceeded the practical runtime ceiling`
- `runtime_ceiling_rule`: `candidate must stay at or below 3x the distilled baseline wall-clock`
- `baseline_wall_clock_seconds`: `240.77`
- `runtime_ceiling_seconds`: `722.31`
- `candidate_dev_observed_elapsed_seconds`: `1086` 
- `decision_note`: `The dev control run crossed the runtime ceiling on the first control clip and still had not produced a completed artifact. That disqualifies dev on practicality. Because dev-two-stage-hq uses the same dev backend with a heavier pipeline, it is dominated on the same gate and was not run on this machine in phase 1.`
- `next_action`: `Open phase 2 with an Apple-native LTX lane, starting with dgrauet/ltx-2.3-mlx on the same control-plus-stress matrix.`

## Motion Review Blocks

### `challenger_short__beat_02a_baseline_control_matrix`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_02a_baseline_control_matrix`
- `archetype`: `field_joint_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_field_joint_closeup_pass_01/20260412T181846Z/challenger_short__beat_02b_field_joint_band_closeup/minimal_surreal_editorial_v3/challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T213336Z-9e0c92b8-comfy-challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T211440Z/clips/first_pass/beat_02a/baseline__seed42.mp4.json`
- `artifact_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T211440Z/clips/first_pass/beat_02a/baseline__seed42.mp4`
- `motion_carrier`: `distilled baseline`
- `source_baked_issue`: `false`
- `disposition`: `keep`
- `failure_reason`: ``
- `next_action`: `Keep this as the current local control baseline for future experiments; do not change production defaults based on this pass alone.`
- `review_note`: `The control clip completed cleanly in 240.77 seconds at 576x1024 and the contact sheet preserves the field-joint geometry without obvious composition drift. This remains the viable local baseline on the current MLX/LTX lane.`

### `challenger_short__beat_02a_candidate_dev_runtime_gate`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_02a_candidate_dev_runtime_gate`
- `archetype`: `field_joint_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_field_joint_closeup_pass_01/20260412T181846Z/challenger_short__beat_02b_field_joint_band_closeup/minimal_surreal_editorial_v3/challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T213336Z-9e0c92b8-comfy-challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: ``
- `motion_carrier`: `dev pipeline on control beat`
- `source_baked_issue`: `false`
- `disposition`: `reject`
- `failure_reason`: `practical runtime gate failure before completion`
- `next_action`: `Do not spend more time on dev or dev-two-stage-hq inside the current MLX/LTX lane on this machine. Move phase 2 to an Apple-native alternative lane instead.`
- `review_note`: `The dev control attempt was allowed to run past 18 minutes on the same beat and still had not emitted a completed clip. That exceeds the experiment ceiling of 722.31 seconds, so it is rejected on practicality even before quality review.`
