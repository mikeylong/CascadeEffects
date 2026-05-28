# Challenger Living Cover Pixel-Exact Lights-Off Masked Relight

Review-only source-art exploration packet.

This packet replaces the prior deterministic lights-off still because the required standard is strict: the lights-off image must literally overlay the lit source plate and be identical except for lighting.

## Source Truth

- Lit source plate: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_exploration/living_cover_launch_pad_realistic_lighting_detail_imagegen_scene_exploration_20260508T002904Z/assets/source_art/realistic_lighting_detail_variant_c.png`
- SHA-256: `dc0fbb6da7596d6374ebed2965d87a9a240b0103a5c740f58efaf208e3fa477a`

## Candidate

- Candidate: `assets/source_art/lights_off_pixel_exact_masked_relight_candidate.png`
- Method: deterministic pixel-space masked relight.
- No `image_gen`, no local generation, no crop, no warp, no rescale, no reframe, no repaint.
- Same `1920x1080` canvas as the source truth.

## Future Ramp Contract

If this still later receives an explicit `keep`, the next proof may use it as the 100% lights-off base and fade the lit plate over it with the story-shaped monotonic opacity curve recorded in the manifest. This packet does not create that proof.

## Review

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

All downstream gates remain locked false.


## Human Reject Note (2026-05-08T02:41:11Z)

Disposition: `reject`. The second-plate masked relight approach created too many image artifacts. It is not an advancement source and is superseded by the single-source render-time light-ramp proof `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_single_source_light_ramp_html_rough_proof_20260508T024111Z`.
