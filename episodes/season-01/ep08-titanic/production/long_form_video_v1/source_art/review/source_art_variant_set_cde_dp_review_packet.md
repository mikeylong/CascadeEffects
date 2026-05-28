# Titanic Source Art Variant Set Review

Workflow: `long_form_video_production_v1`

Living Cover system: `living_cover_system_v1`

Baseline: Canonical Living Cover Baseline v1, Titanic episode baseline loaded before generation.

Status: `review_ready_pending_human_selection`

Current gate: `source_art_keep`

This packet adds Candidates C, D, and E as review variants only. Candidate B remains the current review-ready candidate unless a human selects another source-art plate. No variant is marked `keep`.

## Active Baseline Inputs

- Baseline index: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/index.json`
- Episode baseline: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/titanic.md`
- Current episode TOML: `/Users/mike/Agents_CascadeEffects/episodes/titanic.toml`
- Current source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/source_art_generation_manifest_non_paper_20260519.json`

## Candidate B - Current Review Candidate

- Candidate ID: `candidate_b_lifeboat_davit_readiness`
- Status: `review_ready_pending_human_keep`
- Normalized source art: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_b_lifeboat_davit_readiness_1920x1080.png`
- SHA-256: `41c0aa6bdbab9b5cc8344e460131b81e2cfc01bd1359a8d136f263c5801c9741`
- Review role: baseline comparison and current selected review plate.

## Candidate C - Lifeboat Station Crowd Attention

- Candidate ID: `candidate_c_lifeboat_station_crowd_attention`
- Status: `review_ready_pending_human_selection`
- Normalized source art: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_c_lifeboat_station_crowd_attention_1920x1080.png`
- SHA-256: `fe8a1f33817b3a49e73a751d420b27223eb5f0085f3f6177d98ae8b2ddeced54`
- Review role: wider boat-deck public attention read; stronger anonymous crowd orientation and open right-side sea/sky rail space.
- DP read: `pass_for_review`
- Notes: The frame has more public-scene attention than Candidate B but may be less gear-forward than D/E.

## Candidate D - Davit Block Close Depth

- Candidate ID: `candidate_d_davit_block_close_depth`
- Status: `review_ready_pending_human_selection`
- Normalized source art: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_d_davit_block_close_depth_1920x1080.png`
- SHA-256: `36155b89ab4e057344716d980d4518dcfc69cafe6fdb8c5a16d3448a43e0ed7f`
- Review role: most mechanism-forward carrier; davit block, falls, rope tension, and repeated davits give direct motion affordance.
- DP read: `pass_for_review`
- Notes: Strong machinery readiness. Review should confirm the close foreground crew profile stays non-recognizable at delivery scale.

## Candidate E - Boat Deck Weather Readiness

- Candidate ID: `candidate_e_boat_deck_weather_readiness`
- Status: `review_ready_pending_human_selection`
- Normalized source art: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_e_boat_deck_weather_readiness_1920x1080.png`
- SHA-256: `e5a07275f94c6af4fe374892284042a5efc1b4a932de9be437b2a40588aad38f`
- Review role: strongest weather/practical-light/covered-lifeboat readiness read; repeated davits and wet deck create a clear ambient lane.
- DP read: `pass_for_review`
- Notes: Most polished Living Cover backplate candidate in this set for lamp flicker, wet reflection shimmer, sea haze, and right-rail negative space.

## Required Reads

- `foreground_admin_prop_read`: pass for C/D/E. No foreground clipboard, binder, folder, paperwork stack, legal pad, tray, evidence table, desk, or generic administrative anchor.
- `implied_action_anticipation_read`: pass for C/D/E. Each variant uses lifeboat/davit readiness, rope handling, crew attention, deck activity, or public-scene anticipation.
- `ambient_affordance_read`: pass for C/D/E. Each variant gives later motion credible practical lights, wet reflections, sea/weather surface, rope/fall tension, and restrained human attention.
- `historical/source-reference alignment`: pass for review. All variants remain in an early-1910s ocean-liner boat-deck/lifeboat/davit lane and avoid modern signage or gear.
- `no_recognizable_faces_read`: pass for review. People are rear-facing, distant, cropped, profile-soft, or silhouette-soft; Candidate D should receive the closest human-review check.
- `right_rail_safe_space_read`: pass for review. All variants leave sea/sky/rail space on the right; Candidate E is strongest, Candidate D is acceptable with sea/sky.
- `video_visual_style_scope_read`: pass. These are generated raster source-art review assets for long-form video, not Paper Architecture, Shorts assets, or diagnostic code-native art.
- `paper_architecture_visual_style_read`: pass. No folded-paper, foam-core, paper model, or website-thumbnail-gallery style.

## Gate State

- `may_mark_source_art_keep`: false
- `may_create_cue_map`: false
- `may_create_ambient_effects_layer`: false
- `may_create_music_integration_contract`: false
- `may_start_motion_readiness`: false
- `may_start_rough_assembly`: false
- `may_render_final_mp4`: false
- `may_youtube_action`: false
- `public_release_ready`: false

## Human Disposition Needed

Choose one:

- `keep source art candidate B`
- `keep source art candidate C`
- `keep source art candidate D`
- `keep source art candidate E`
- `tighten source art`
- `reject source art variants`
