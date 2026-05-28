# Hyatt Regency Living Cover Visual System Baseline

Episode ID: `hyatt-regency`

Baseline status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`

## Active Source Art

- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/assets/source_art/n6_architecture_crowd_density_1920x1080.png`
- Active source art SHA-256: `1bbdebe0fdc425f387f2f218633501ab3ce7d5fa5bad8b9a36f989b6eb30bae4`
- Source manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/source_art_manifest.json`
- Source manifest SHA-256: `6c39560144640c797360457324404956e2dc2ba808be172fdf1d6bf7d3199a78`
- Style lane: `cascade-ink-lit-photoreal-v1`

## Canonical Read

The active Hyatt Regency Living Cover backplate is N6, the architecture/crowd-density source art. It replaces N5B and fixes the prior top-walkway/floor mismatch and underpopulated atrium problem.

The baseline must read as a plausible Hyatt atrium during the tea dance: stacked second and fourth suspended walkways, offset third walkway geometry, visible hanger rods and load-path implications, crowded main floor density, table decor, and anonymous human presence on the floor, walkways, and balconies. The right side remains dark enough for the fixed rail without turning into a generic opaque panel.

Required source-art reads:

- `hyatt_atrium_architecture_read: pass`
- `stacked_second_fourth_walkways_read: pass`
- `offset_third_walkway_read: pass`
- `hanger_rod_load_path_read: pass`
- `tea_dance_density_read: pass`
- `table_decor_read: pass`
- `human_presence_read: pass`
- `no_recognizable_faces_read: pass`
- `right_rail_safe_space_read: pass`
- `video_visual_style_scope_read: pass`
- `paper_architecture_visual_style_read: pass`

Hard blockers:

- floating walkway
- sparse atrium occupancy
- recognizable faces
- collapse, broken walkway, emergency aftermath, bodies, gore, or rescue scene
- fake readable signage, text, documents, or labels
- diagnostic cyan overlays or visible load-path graphics on the source plate

## Ambient And Effects Lane

The active rough-proof ambient lane uses user-marked regions for camera flashes and balloon rises, with Challenger-staged visual transitions preserved. Ambient additions must stay public-scene plausible and must not turn into collapse foreshadowing, diagnostic overlays, or source-plate repainting.

## Rail And End Screen

- Living Cover system: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- End-screen template: `challenger_titleless_end_screen_overlay_on_living_cover_v1`
- Transition precedent: Challenger-staged transitions
- Music/outro transition: `subtle_tail_outro_v1`

The titleless three-target end screen remains the default. Current publish-readiness tightening is audio/VO-outro related and does not invalidate the kept N6 visual baseline.

## Known Superseded Artifact

- N5B source art: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_variant_n_believable_table_bouquets_20260517T051623Z/assets/source_art/n5b_plausible_table_centerpieces_1920x1080.png`
- Superseded reason: top walkway/floor mismatch and insufficient tea-dance crowd density.
- Active status: `false`

## Current Blockers

- Visual baseline is active.
- Publish-readiness package still carries audio/VO-outro tightening, not a source-art replacement requirement.

<!-- rolling-caption-rail-redesign:start -->

## Rolling Caption Rail Redesign

- Rollout date: `2026-05-20`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Action: `supersede_publish_final_surfaces_create_successor_rough_proof`
- Successor rough manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
- Successor player: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260523T182309Z/player.html`
- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/assets/source_art/n6_architecture_crowd_density_1920x1080.png`
- Active source art SHA-256: `1bbdebe0fdc425f387f2f218633501ab3ce7d5fa5bad8b9a36f989b6eb30bae4`

- Source art rollback: not opened by default; revalidate right-rail safe space only.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until the refreshed rough proof receives human `keep`.


<!-- rolling-caption-rail-redesign:end -->
