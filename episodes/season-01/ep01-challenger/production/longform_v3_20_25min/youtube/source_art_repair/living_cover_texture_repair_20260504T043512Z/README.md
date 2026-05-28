# Challenger Living Cover Texture Repair Stills

Status: `blocked_stale_daylight_profile_reference_only`

Gate: `source_art_repair_gate`

Selected direction: `Living Cover`

Still review only: `true`

Human disposition: `keep`

Selected variant: `B`

Selected variant texture_noise_read: `pass`

Selected variant visual_profile_read: `tighten_stale_daylight_profile`

Superseded by first ink-lit repair packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_ink_lit_repair_20260504T061353Z`

Current replacement review packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_dry_signal_repair_20260504T163347Z`

May replace current source art: `false`

May swap into rough player: `false`

## Why This Exists

The current Living Cover raster source art is blocked as `texture_noise_read: tighten`. The prompt and brand contracts already contained the no-noise guardrail, so this packet treats the failure as QA/disposition enforcement rather than missing prompt language.

No denoise or texture filter was used. These are fresh generated raster/source-art candidates.

## Review Contact Sheets

- `320x180`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/qa/contact_sheet_320x180.png`
- `168x94`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/qa/contact_sheet_168x94.png`

## Variants

| Variant | Source art | Texture read | Note |
|---|---|---:|---|
| A | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/assets/source_art/living_cover_clean_variant_a.png` | `defer` | Balanced left anchor with midground evidence sheets. |
| B | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/assets/source_art/living_cover_clean_variant_b.png` | `pass` | `keep`; strongest right-rail negative space. |
| C | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/assets/source_art/living_cover_clean_variant_c.png` | `defer` | Adds a small O-ring-like evidence object. |

## Gate Rule

Variant B has human `keep` and `texture_noise_read: pass`, but it is now composition reference only because it fails the current ink-lit profile read. The first ink-lit repair packet is also blocked by `waterfall_read: tighten`. Full-runtime rough, MP4 render, and final assembly remain blocked until a dry-signal ink-lit still receives human `keep` with `texture_noise_read: pass`, `visual_profile_read: pass`, and `waterfall_read: pass`.
