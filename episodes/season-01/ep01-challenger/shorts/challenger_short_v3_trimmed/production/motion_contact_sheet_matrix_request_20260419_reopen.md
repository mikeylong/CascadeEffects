# Challenger Reopened Dual LTX2 Motion Contact Sheet Request

## Request

- `episode_id`: `challenger`
- `short_id`: `challenger_short_minimal_surreal_v3_trimmed`
- `request_stage`: `motion contact sheet`
- `request_disposition`: `diagnostic only`
- `reopen_reason`: `the 20260419T010520Z keeper proof was reviewed before the dual-model motion contact-sheet matrix policy existed; the workflow change was prompted by Challenger review`
- `governing_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md`
- `style_skill_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/SKILL.md`
- `promotion_workflow_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/judgment/promotion_workflow.md`
- `source_manifest_path`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_minimal_surreal_v3_trimmed.json`
- `prior_motion_proof_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T010520Z/20260419T010520Z__proof.mp4`
- `prior_video_final_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T010520Z/final_exports/challenger_final_v1/20260419T011005Z__captioned_final.mp4`
- `prior_state`: `paused keeper candidate; not publish-terminal while this reopened contact sheet is open`
- `planned_output_root`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed_motion_contact_sheet_dual_ltx2_reopen_20260419`

## Gate

- `baseline_motion_pipeline`: `distilled`
- `baseline_model_repo`: `mlx-community/LTX-2-distilled-bf16`
- `comparison_motion_pipeline`: `apple-ltx23-q8-one-stage`
- `comparison_model_repo`: `dgrauet/ltx-2.3-mlx-q8`
- `comparison_text_encoder_repo`: `mlx-community/gemma-3-12b-it-4bit`
- `matrix_rule`: `for each eligible source still, render two distilled candidates and two Apple LTX2.3 candidates`
- `seed_rule`: `use the same two seed slots for both model families on the same beat and source still`
- `prompt_rule`: `candidate A uses the canonical beat motion prompt; candidate B uses the beat-class stability prompt`
- `proof_rule`: `do not build or re-approve a timed motion video proof until the contact sheet has selected keep winners`
- `backend_rule`: `beat_01b remains a beat-local Apple-native exception; it does not authorize a short-wide backend swap`

## Reopened Scope

Mandatory reopened matrix beats:

- `beat_02b`: current proof uses a reviewed locked hold because motion drifted into premature ignition/plume behavior.
- `beat_04a`: current proof uses a reviewed locked hold to preserve localized seam smoke with no widened launch context.
- `beat_04b`: current proof uses a reviewed locked hold to preserve canonical in-flight shuttle anatomy and the visible flame read.
- `beat_05`: current proof uses a reviewed locked hold, but Challenger review already identified the control-room carrier as motion-brittle; include the `parts-bin witness` still candidate as the alternate lane once approved.

Optional diagnostic audit beats:

- `beat_01b`: keep the Apple-native winner as the live exception, but include a matched distilled-vs-Apple audit only if the proof reviewer wants direct evidence in the reopened contact sheet.
- `beat_03`: existing recovered distilled motion remains the live keeper; include a human/tableau comparison only if the decision-room motion is reopened.

Excluded by default:

- `beat_04c`: keep the exact NASA 86-HC-220 crop as a reviewed locked historical hold. Do not render generated 04c motion unless the crop fails editorial timing.
- `beat_01a` and `beat_02a`: current distilled motion keepers can carry forward unchanged unless the full proof is reopened beyond the locked-hold beats.

## Candidate Matrix

| beat_id | source_still_variant_role | source_still_path | motion_class | seed_a | seed_b | render_status |
| --- | --- | --- | --- | --- | --- | --- |
| `beat_02b` | `primary` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_context_cleanup_pass_01/20260412T202354Z/challenger_short__beat_02b_tank_calm_context/minimal_surreal_editorial_v3/challenger_short__beat_02b_tank_calm_context__minimal_surreal_editorial_v3_00001_.png` | `locked context` | `74201` | `74202` | `render` |
| `beat_02b` | `alternate` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_02b_context_cleanup_pass_01/20260412T202015Z/challenger_short__beat_02b_clean_mid_stack_hold/minimal_surreal_editorial_v3/challenger_short__beat_02b_clean_mid_stack_hold__minimal_surreal_editorial_v3_00001_.png` | `locked context` | `74211` | `74212` | `render` |
| `beat_04a` | `primary` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_04_exterior_restage_pass_01/20260414T183422Z/challenger_short__beat_04a_joint_smoke_seep/minimal_surreal_editorial_v3/challenger_short__beat_04a_joint_smoke_seep__minimal_surreal_editorial_v3_00001_.png` | `documentary anomaly` | `74401` | `74402` | `render` |
| `beat_04a` | `alternate` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_04_visible_failure_pass_02/20260411T220102Z/challenger_short__beat_04_tower_side_joint_smoke/minimal_surreal_editorial_v3/challenger_short__beat_04_tower_side_joint_smoke__minimal_surreal_editorial_v3_00001_.png` | `documentary anomaly` | `74411` | `74412` | `render only as diagnostic alternate; reject if widened context weakens the localized seam read` |
| `beat_04b` | `primary` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_04_exterior_restage_pass_01/20260414T183422Z/challenger_short__beat_04b_flight_flame_visible/minimal_surreal_editorial_v3/challenger_short__beat_04b_flight_flame_visible__minimal_surreal_editorial_v3_00001_.png` | `documentary anomaly` | `74421` | `74422` | `render` |
| `beat_04b` | `alternate` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_04_visible_failure_pass_02/20260411T220102Z/challenger_short__beat_04_front_profile_breach/minimal_surreal_editorial_v3/challenger_short__beat_04_front_profile_breach__minimal_surreal_editorial_v3_00001_.png` | `documentary anomaly` | `74431` | `74432` | `render only as diagnostic alternate; reject if anatomy or chronology drifts` |
| `beat_05` | `primary` | `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_challenger_short_beat_05_systemic_thesis_pass_04/20260412T015508Z/challenger_short__beat_05_indicator_block_wall/minimal_surreal_editorial_v3/challenger_short__beat_05_indicator_block_wall__minimal_surreal_editorial_v3_00001_.png` | `locked context` | `74501` | `74502` | `render only if reviewer still wants the current control-room carrier compared` |
| `beat_05` | `alternate` | `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed_motion_feedback_pass_15/still_candidates/beat_05_parts_bin_witness/beat_05_parts_bin_witness__seed24170511__beat_05_parts_bin_witness_seed24170511_00001_.png` | `locked context` | `74511` | `74512` | `do not render until this still is approved as keep` |

For every rendered row above, create these four candidates:

| motion_pipeline | model_repo | text_encoder_repo | prompt_variant_id | seed |
| --- | --- | --- | --- | --- |
| `distilled` | `mlx-community/LTX-2-distilled-bf16` | `not applicable` | `canonical_a` | `seed_a` |
| `distilled` | `mlx-community/LTX-2-distilled-bf16` | `not applicable` | `stability_b_<motion_class>` | `seed_b` |
| `apple-ltx23-q8-one-stage` | `dgrauet/ltx-2.3-mlx-q8` | `mlx-community/gemma-3-12b-it-4bit` | `canonical_a` | `seed_a` |
| `apple-ltx23-q8-one-stage` | `dgrauet/ltx-2.3-mlx-q8` | `mlx-community/gemma-3-12b-it-4bit` | `stability_b_<motion_class>` | `seed_b` |

## Stability Prompt Variants

- `stability_b_locked_context`: `locked camera and fixed room or vehicle geometry; the approved still composition stays fixed; allow only restrained light, haze, vent, dust, or lamp drift that does not rewrite the scene; no readable text, no UI, no camera flourish`
- `stability_b_documentary_anomaly`: `canonical hardware anatomy and chronology stay fixed; the existing anomaly remains localized and physically readable; allow only small plume, haze, heat, soot, or light movement already implied by the still; no added spectacle, no breakup unless the beat explicitly requires it`
- `stability_b_human_tableau`: `concrete roles and fixed positions; figures, table, walls, whiteboard, and furniture stay in place; allow only restrained hand/head changes when present; no writing, no letters, no numbers, no new furniture, no sit-stand action`

## Review Contract

The rendered motion contact sheet note must group candidates by `beat_id`, `source_still_path`, `source_still_variant_role`, `motion_pipeline`, `prompt_variant_id`, and `seed`. Each candidate record must include:

- `beat_id`
- `source_still_path`
- `source_still_variant_role`
- `motion_pipeline`
- `model_repo`
- `text_encoder_repo` when `motion_pipeline` is `apple-ltx23-q8-one-stage`
- `seed`
- `prompt_variant_id`
- `prompt_text` or `prompt_path`
- `raw_clip_path`
- `normalized_clip_path`
- `disposition`
- `selected_for_motion_proof`

Initial `disposition` for unreviewed comparison candidates is `diagnostic only`; initial `selected_for_motion_proof` is `false`. Only reviewed `keep` winners may enter the replacement timed motion proof and then a replacement `video final`.
