# Challenger Local Motion Quality Experiment Pass 02 Apple LTX 2.3

- `review_date`: `2026-04-14`
- `experiment_id`: `local_motion_quality_challenger_phase2_apple_ltx23`
- `run_root`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T224430Z`
- `baseline_summary_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T211440Z/summary.json`
- `result`: `beat_01b-only Apple-native exception; global baseline remains distilled`
- `control_runtime_ceiling_seconds`: `722.31`

### `challenger_short__beat_02a_apple_ltx23_q8_one_stage`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_02a_apple_ltx23_q8_one_stage`
- `archetype`: `field_joint_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_field_joint_closeup_pass_01/20260412T181846Z/challenger_short__beat_02b_field_joint_band_closeup/minimal_surreal_editorial_v3/challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T230141Z-ce018745-comfy-challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T224430Z/clips/control/beat_02a/q8_one_stage__seed42.mp4`
- `motion_carrier`: `challenger_short__beat_02a_apple_ltx23_q8_one_stage`
- `source_baked_issue`: `false`
- `disposition`: `keep`
- `failure_reason`: ``
- `next_action`: `treat as a completed control check only; do not replace the distilled baseline from this result`
- `review_note`: `The control clip stays canonical and stable. It is visually close to the distilled baseline rather than dramatically better, but it remains within the practical runtime ceiling and is strong enough to support the stress comparison.`

### `challenger_short__beat_02a_apple_ltx23_q8_hq`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_02a_apple_ltx23_q8_hq`
- `archetype`: `field_joint_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_field_joint_closeup_pass_01/20260412T181846Z/challenger_short__beat_02b_field_joint_band_closeup/minimal_surreal_editorial_v3/challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T230141Z-ce018745-comfy-challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: ``
- `motion_carrier`: `challenger_short__beat_02a_apple_ltx23_q8_hq`
- `source_baked_issue`: `false`
- `disposition`: `reject`
- `failure_reason`: `did not complete before the practical runtime ceiling`
- `next_action`: `do not use HQ on this machine for this lane`
- `review_note`: `The HQ pass timed out at the same 722.31 second ceiling used for the control gate and produced no clip, so it fails the practicality test outright.`

### `challenger_short__beat_01b_apple_ltx23_q8_one_stage`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_01b_apple_ltx23_q8_one_stage`
- `archetype`: `cold_launch_site_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_01_cold_launch_site_pass_02/20260412T030807Z/challenger_short__beat_01_blue_haze_hold/minimal_surreal_editorial_v3/challenger_short__beat_01_blue_haze_hold__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T230141Z-6450a350-comfy-challenger_short__beat_01_blue_haze_hold__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T224430Z/clips/stress/beat_01b/q8_one_stage__seed42.mp4`
- `motion_carrier`: `challenger_short__beat_01b_apple_ltx23_q8_one_stage`
- `source_baked_issue`: `false`
- `disposition`: `keep`
- `failure_reason`: ``
- `next_action`: `advance this lane only as the beat_01b hard-case exception and run winner-seed verification`
- `review_note`: `This is the decisive improvement in the experiment. The clip preserves the fixed launch-site composition and removes the bird-swarm takeover that dominates the current active beat_01b motion lane, while keeping haze drift and service-light motion restrained.`

### `challenger_short__beat_02a_apple_ltx23_q8_one_stage_seed314159`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_02a_apple_ltx23_q8_one_stage_seed314159`
- `archetype`: `field_joint_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_field_joint_closeup_pass_01/20260412T181846Z/challenger_short__beat_02b_field_joint_band_closeup/minimal_surreal_editorial_v3/challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T230141Z-ce018745-comfy-challenger_short__beat_02b_field_joint_band_closeup__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T224430Z/clips/winner_seed/beat_02a/q8_one_stage__seed314159.mp4`
- `motion_carrier`: `challenger_short__beat_02a_apple_ltx23_q8_one_stage_seed314159`
- `source_baked_issue`: `false`
- `disposition`: `keep`
- `failure_reason`: ``
- `next_action`: `record robustness as acceptable on the control lane`
- `review_note`: `The second-seed control rerun remains canonical and stable, confirming that the Apple-native winner is not relying on a one-off seed for the easy case.`

### `challenger_short__beat_01b_apple_ltx23_q8_one_stage_seed314159`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`: `challenger`
- `case_id`: `challenger_short__beat_01b_apple_ltx23_q8_one_stage_seed314159`
- `archetype`: `cold_launch_site_motion`
- `source_asset`: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_01_cold_launch_site_pass_02/20260412T030807Z/challenger_short__beat_01_blue_haze_hold/minimal_surreal_editorial_v3/challenger_short__beat_01_blue_haze_hold__minimal_surreal_editorial_v3_00001_.png`
- `staged_asset`: `/Users/mike/AI/outputs/handoff/20260414T230141Z-6450a350-comfy-challenger_short__beat_01_blue_haze_hold__minimal_surreal_editorial_v3_00001_.png`
- `video_manifest`: ``
- `artifact_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/experiments/local_motion_quality/20260414T224430Z/clips/winner_seed/beat_01b/q8_one_stage__seed314159.mp4`
- `motion_carrier`: `challenger_short__beat_01b_apple_ltx23_q8_one_stage_seed314159`
- `source_baked_issue`: `false`
- `disposition`: `keep`
- `failure_reason`: ``
- `next_action`: `record Apple-native one-stage as a beat_01b-only exception; keep the distilled/current proven lane as the global baseline and keep airborne-fleck suppression in scope for this beat`
- `review_note`: `The second-seed stress rerun keeps the pad-held composition and avoids a full return to the previous bird-swarm failure mode. Small airborne flecks remain visible in isolated frames, but the result does not collapse or reverse the first-pass improvement.`
