# 737 MAX Lion Air Livery Review Variant

status: source_art_review_variant_wired_into_rough_rail_review_pending_human_keep
episode_id: 737-max
created_utc: 2026-05-22T03:46:00Z
variant_scope: rough_rail_review_only
active_proof_rebuilt: true
rolling_caption_packet_changed: true
final_assembly_gate_changed: false
publish_or_youtube_gate_changed: false

## Source

- Source plate: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_l_ramp_depth_lights_1920x1080_20260519.png`
- Source plate sha256: `05519145f11d4ceb49d38d6684fcb029877fca0bcec2329165eb81ff317a28b4`
- Imagegen raw output: `/Users/mike/.codex/generated_images/019e479d-6151-7493-9187-1e8f42123d90/ig_0f76125c36a9ba4d016a0fd139df2081939c2a053160c89bd6.png`
- Imagegen raw output sha256: `58f322ef52933453addcb7ad1e2e1bdf0f5d36674c4b901da7fed82eef23e4ac`

## Review Variant

- 1920x1080 variant: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_l_lion_air_livery_review_variant_20260522.png`
- 1920x1080 sha256: `4968848f244e5ea92e6c80e1dd5a63aaa404db52994f98a622d3a9839d5b24b6`
- 320x180 preview: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/review/737_max_candidate_l_lion_air_livery_review_variant_preview_320x180_20260522.png`
- 168x94 preview: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/review/737_max_candidate_l_lion_air_livery_review_variant_preview_168x94_20260522.png`

## Wired Proof

- Rough proof path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly/737-max_rolling_caption_rail_rough_proof_20260520T235500Z/player.html`
- Rough manifest path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly/737-max_rolling_caption_rail_rough_proof_20260520T235500Z/rough_assembly_manifest.json`
- Wiring model: `source_art_override_wired_into_generated_rough_proof`
- Keep state: `pending_human_keep`

## Prompt

Use case: precise-object-edit.

Edit the clean 1920x1080 737 MAX source plate only. Add exact Lion Air livery to the visible aircraft: red vertical tail with white lion mark, red Lion Air fuselage wordmark, and matching red livery striping. Preserve the rainy terminal glass, mullions, people silhouettes, ramp lighting, wet reflections, plane geometry, cockpit/window alignment, engine, wing, and right-rail safe space. Do not add captions, UI, unrelated signage, extra aircraft, or watermarks.

## QA Reads

- source_plate_preservation_read: pass_for_review
- lion_air_livery_read: pass_for_review_pending_human_keep
- right_rail_text_artifact_read: pass_no_caption_or_ui_text_added
- review_preview_1920x1080_read: pass_generated
- review_preview_320x180_read: pass_generated
- review_preview_168x94_read: pass_generated
- rough_rail_source_art_override_read: pass_source_art_override_wired_into_generated_rough_proof
- active_rough_proof_gate_read: pending_human_keep

## Gate Note

This variant is now wired into the rolling-caption rough proof for review. It is still not a source-art keep, final-assembly approval, publish-readiness approval, or YouTube action approval until a human explicitly keeps the refreshed rough proof and later gates.
