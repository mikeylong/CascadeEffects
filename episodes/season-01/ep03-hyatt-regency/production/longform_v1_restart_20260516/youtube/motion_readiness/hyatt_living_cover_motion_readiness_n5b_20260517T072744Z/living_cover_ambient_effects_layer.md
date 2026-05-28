# Hyatt Living Cover Ambient Effects Layer

Status: `review_ready_internal_artifact`
Human disposition: `defer`

This packet defines restrained source-integrated motion for the N5B Hyatt Living Cover. It does not create a rough proof and does not authorize MP4 rendering or upload.

## Source Carrier

![N5B source-art carrier](/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_variant_n_believable_table_bouquets_20260517T051623Z/assets/source_art/n5b_plausible_table_centerpieces_1920x1080.png)

- Source-art SHA-256: `7b6f6c5aa1970f311e01676d45e03a5bf319a11482e4d80531cfb266504b9458`
- Coordinate space: fixed `1920x1080`
- Carrier policy: preserve the source-art plate; do not redraw the atrium, people, walkways, hanger rods, balloons, or load path as procedural art.

## Selected Lanes

- Source drift/lighting: slow, nearly imperceptible parallax and warm practical-light breathing.
- Subtle depth particles: sparse dust or light flecks that never read as evidence, sparks, collapse debris, or water.
- Event micro-life: only source-plate lighting/parallax cues; no generated faces or new people.
- Music/visual handoff: soften rail and suppress captions during the outro/end-screen window.

## Forbidden Output

- No cyan load-path overlays on the source plate.
- No route overlays, debug labels, matte previews, implementation panels, or effect-lane names in viewer output.
- No collapse recreation, emergency imagery, bodies/gore, fake readable text, or recognizable faces.
- No broad full-frame dark veil; readability treatment stays localized to rail/title/caption areas.

## Browser QA Plan

A future rough proof must be served through localhost and sampled at `0`, `82`, `181`, `298`, `475`, `753`, `818.643`, and `832.643` seconds before rough-proof keep can be recorded.

## Reads

- `ambient_effects_plan_read`: `pass`
- `ambient_effect_lane_decision_read`: `pass_mixed_restrained_source_integrated`
- `source_plate_matte_registration_read`: `pass_planned_same_fixed_coordinate_space`
- `foreground_occlusion_read`: `pass_planned_no_new_human_detail`
- `effect_layer_source_safety_read`: `pass`
- `deterministic_ambient_read`: `pass_seeded_parameters_recorded`
- `additive_effect_integration_read`: `pass`
- `debug_overlay_absence_read`: `pass`
- `ambient_effect_browser_sample_read`: `planned_required_before_rough_keep`
- `range_scrub_effect_review_read`: `planned_required_before_rough_keep`
