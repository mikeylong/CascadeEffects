# 737 MAX Human Source-Art Tighten - Candidate J Right-Rail Block

Date: 2026-05-19

Reviewed at UTC: 2026-05-19T16:55:04Z

Workflow: `long_form_video_production_v1`

Gate: `source_art_candidate_review`

Human disposition: `tighten`

Candidate: `candidate_j_terminal_ramp_attention`

Candidate set: `candidate_set_g_to_j_action_ambient`

## Human Review Basis

The prior `keep` on `candidate_j_terminal_ramp_attention` is superseded by human review feedback:

> I'm bothered by the solid gray block on the right hand side of 737 MAX Candidate J

This is a source-art carrier issue. It should not be repaired in the cue map by hiding the plate with rail treatment, and it should not advance into ambient/effects planning.

## Tighten Finding

Candidate J has strong subject/event presence, terminal/ramp attention, anonymous human presence, and weather/lighting affordance. The right side, however, reads as a solid gray vertical block rather than integrated public-scene negative space.

That creates a Living Cover problem:

- the right side feels like a placeholder panel instead of part of the source scene
- the rail-safe area is too visually dead for a living-cover backplate
- the area gives weak ambient affordance compared with rain glass, ramp lights, terminal depth, or runway/service motion
- the plate risks normalizing a full-height opaque rail column, which the current long-form visual style rules treat as a `tighten` condition

## Source-Art Reads

- `right_rail_safe_space_read`: `tighten_solid_gray_block_not_scene_integrated_negative_space`
- `right_rail_opacity_balance_read`: `tighten_source_visibility_too_low_on_right_side`
- `context_region_source_visibility_read`: `tighten_right_context_area_reads_as_opaque_column`
- `rail_backlight_scope_read`: `tighten_repair_before_rail_or_cue_map_advancement`
- `ambient_affordance_read`: `tighten_right_side_lacks_credible_living_cover_micro_life`
- `implied_action_anticipation_read`: `pass_left_center_terminal_ramp_attention`
- `foreground_admin_prop_read`: `pass_no_dominant_foreground_admin_props`
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`

## Affected Artifacts

- Candidate J plate: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_j_terminal_ramp_attention_1920x1080_20260519.png`
- Candidate J plate SHA-256: `b8c181845825e38133bc80b2e518be5b11603de3289fa22307cc1268859df1b0`
- Prior human keep note: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/review/human_source_art_keep_candidate_j_terminal_ramp_attention_20260519.md`
- Prior human keep note SHA-256: `aac25605e0aeba53df646c17a02800e4bf593e2e0a38833060397cc2cbcc26bc`
- Prior keep manifest: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/source_art_candidate_j_terminal_ramp_attention_keep_manifest_20260519.json`
- Prior keep manifest SHA-256: `79003826f0c57aa930afa5fb35d85024a087191111c3fe222a384bad27703124`
- Candidate J cue map: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_j_terminal_ramp_attention_20260519.md`
- Candidate J cue map SHA-256: `9acacdf114850cb9003c587565894269bd31269d2be2c17d3752b10fcf917568`

## Gate Effect

- `source_art_keep_status`: `tighten`
- `candidate_j_status`: `tighten_reference_only`
- `living_cover_cue_map_status`: `superseded_blocked_by_source_art_tighten`
- `current_gate_after_tighten`: `source_art_generation`
- `next_required_gate`: `candidate_k_to_n_right_rail_repair_generation`
- `may_generate_source_art`: `true`
- `may_mark_source_art_keep`: `false`
- `may_create_cue_map`: `false`
- `may_create_ambient_effects_layer`: `false`
- `may_create_music_integration_contract`: `false`
- `may_start_motion_readiness`: `false`
- `may_start_rough_assembly`: `false`
- `may_render_final_mp4`: `false`
- `may_youtube_action`: `false`
- `may_public_release`: `false`

## Repair Direction

Reopen source-art generation for a small right-rail repair set. New candidates must preserve the DP/Living Cover direction while replacing the blocky right side with integrated, rail-safe scene depth:

- dark rain glass with visible reflection gradients, terminal mullions, runway/ramp lights, or wet tarmac depth
- not a flat wall, opaque column, blank gray slab, full-height rail panel, or placeholder backdrop
- right side remains low-detail enough for `fixed_16x9_right_rail_v1`, but visibly belongs to the same scene
- preserve anonymous human presence, public-scene attention, unbranded 737 MAX-family nose/engine geometry, non-Paper style, no readable text/logos, no crash/wreckage/fire, and no recognizable faces
