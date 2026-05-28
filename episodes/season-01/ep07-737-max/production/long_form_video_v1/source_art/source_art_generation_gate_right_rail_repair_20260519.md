# 737 MAX Source-Art Generation Gate - Right-Rail Repair

Date: 2026-05-19

Created at UTC: 2026-05-19T16:55:04Z

Workflow: `long_form_video_production_v1`

Gate: `source_art_generation`

Status: `open_pending_generation`

May advance: `false`

## Why This Gate Reopened

Candidate J was previously kept, but human review tightened it because the right side reads as a solid gray block. That issue belongs in source-art generation, not in the cue map or ambient/effects layer.

## Active Repair Target

Generate a small review set, `candidate_k` through `candidate_n`, that preserves the successful parts of Candidate J while repairing the right side.

Successful elements to preserve:

- recognizable unbranded 737 MAX-family nose/engine geometry
- larger forward/high-mounted engine relationship
- anonymous public-scene/human presence
- terminal/ramp attention and readiness before departure
- rain glass, wet tarmac, practical lights, and reflective aviation environment
- non-Paper, source-preserving photoreal Living Cover carrier

Required repair:

- the right side must remain rail-safe but cannot be a solid gray block, blank wall, opaque vertical slab, full-height rail column, or placeholder panel
- right side should contain low-detail integrated scene depth: dark rain glass, terminal mullions, reflection gradients, ramp/runway lights, distant vehicles, weather surface, or atmospheric public-scene depth

## Required Reads Before Source-Art Keep

- `right_rail_safe_space_read`
- `right_rail_opacity_balance_read`
- `context_region_source_visibility_read`
- `rail_backlight_scope_read`
- `foreground_admin_prop_read`
- `implied_action_anticipation_read`
- `ambient_affordance_read`
- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `737_max_aircraft_profile_read`
- `leap_engine_placement_read`
- `angle_of_attack_sensor_cue_read`
- `mcas_stabilizer_mechanism_read`
- `single_sensor_assumption_read`
- `training_commonality_document_cue_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `generated_text_logo_read`
- `no_crash_spectacle_read`
- `video_visual_style_scope_read`
- `paper_architecture_visual_style_read`
- `texture_noise_read`
- `waterfall_read`

## Gate Locks

- `may_generate_source_art`: `true`
- `may_mark_source_art_keep`: `false`
- `may_create_cue_map`: `false`
- `may_create_ambient_effects_layer`: `false`
- `may_create_music_integration_contract`: `false`
- `may_start_motion_readiness`: `false`
- `may_start_rough_assembly`: `false`
- `may_render_final_mp4`: `false`
- `may_youtube_action`: `false`
- `public_release_ready`: `false`
