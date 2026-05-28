# Challenger Living Cover Texture Repair Review

Gate: `source_art_repair_gate`

Status: `blocked_stale_daylight_profile_reference_only`

Selected visual direction: `Living Cover`

Motion scope: `false`

HTML-to-video scope: `false`

Human disposition: `keep`

Selected variant: `B`

Selected variant texture_noise_read: `pass`

Selected variant visual_profile_read: `tighten_stale_daylight_profile`

Superseded by ink-lit repair packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_ink_lit_repair_20260504T061353Z`

## Current Blocker

The current Living Cover raster source art is `texture_noise_read: tighten` because the surface texture is too dominant under the subtle-paper-fiber-only rule.

The existing prompt and contracts already included: `subtle paper fiber only, clean low-detail paper planes, no speckle/noise/grain/grit/sandy texture`. The correction is stricter QA/disposition enforcement plus fresh source-art candidates, not a denoise/filter pass.

## Contact Sheets

| Scale | Path |
|---|---|
| `320x180` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/qa/contact_sheet_320x180.png` |
| `168x94` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z/qa/contact_sheet_168x94.png` |

## Variant Reads

| Variant | Public anchor | Right rail safe space | Text/logo/watermark | texture_noise_read | Disposition |
|---|---:|---:|---:|---:|---:|
| A | `pass_candidate` | `pass_candidate` | `pass_visual_precheck` | `defer` | `defer` |
| B | `pass` | `pass` | `pass` | `pass` | `keep` |
| C | `pass_candidate` | `pass_candidate` | `pass_visual_precheck` | `defer` | `defer` |

## Disposition

Mike selected Variant B as `keep` with `texture_noise_read: pass` before the active profile changed to `cascade-paper-architectures-ink-lit-v1`.

Variant B is now composition reference only. It was generated from daylight/peach/mint prompt language, and the first ink-lit repair packet is also blocked by `waterfall_read: tighten`, so rough-player replacement, MP4 rendering, full-runtime rough, and final assembly remain blocked until a dry-signal ink-lit replacement still receives human `keep` with `texture_noise_read: pass`, `visual_profile_read: pass`, and `waterfall_read: pass`.
