# Challenger Living Cover Crew Liveliness HTML Rough Review

Packet: `living_cover_photoreal_ink_lit_full_runtime_crew_liveliness_html_rough_proof_20260505T170441Z`
Gate: `rough_assembly_gate`
Status: `review_ready_pending_human_crew_liveliness_html_rough_keep`
Human disposition: `defer`

## What Changed

- Current staged-rail HTML proof is recorded as `tighten`.
- The issue is crew liveliness: the foreground astronauts still read too static for a Living Cover.
- The kept Variant C raster remains the background/source carrier.
- Seven transparent foreground astronaut sprites are extracted from the existing crew area and overlaid in place.
- Crew motion is restrained and staggered: weight shifts, small whole-body pivots, torso/shoulder settling, and contact-shadow changes.
- The staged rail, YouTube-legible text, no progress bars, no gradients/vignettes, and `window.__setRenderTime` are preserved.
- Audio, captions, transcript, and full `00:21:29.131` timing are referenced in place.

## Player

- HTML proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_crew_liveliness_html_rough_proof_20260505T170441Z/player.html`
- Uses `window.__setRenderTime` for deterministic QA.
- References full audio/captions/transcript in place.

## Section Map

| # | Start | Section | Purpose |
|---:|---:|---|---|
| 1 | `00:00` | First Warning | A small clue becomes the entry point. |
| 2 | `01:29` | Cold Joint | Cold changes how the seal responds. |
| 3 | `03:03` | Joint Problem | Known damage becomes operating history. |
| 4 | `05:38` | Warning Becomes Process | Damage is translated into procedure. |
| 5 | `08:39` | Processed Warning | Familiar risk starts to feel normal. |
| 6 | `10:29` | Launch-Night Decision | Evidence must prove more than concern. |
| 7 | `13:28` | Recommendation Reversal | The same chain returns a new answer. |
| 8 | `18:02` | Routine Pressure | Memory loses control over behavior. |

## QA Reads

| Read | Result |
|---|---:|
| top timecode removed | `pass` |
| full runtime structure | `pass` |
| baked progress bars | `pass_no_rail_signal_or_bottom_progress_dom_css` |
| gradients/vignette | `pass_no_linear_radial_gradient_or_atmosphere_layer` |
| staged transition | `pass_120_360_600ms_rail_build` |
| layout reflow jitter | `pass_no_font_size_max_height_display_or_padding_transition` |
| multi-build sequence | `pass_outgoing_title_body_phases` |
| transition speed | `pass_600ms_total_staged_crossover` |
| crew count | `pass_exactly_seven_foreground_motion_sprites` |
| crew liveliness | `defer_pending_human_review` |
| crew motion authenticity | `defer_pending_human_review` |
| uncanny motion | `defer_pending_human_review` |
| identity/logo/text | `pass_no_new_text_name_patch_logo_or_face_layer_added` |
| foreground occlusion | `pass` |
| right rail safe space | `pass` |
| active summary size target | `22px` |
| active current-subbeat size target | `25px` |
| computed active text minimum | `pass` |
| YouTube legibility | `defer_pending_human_review` |
| compression resilience | `defer_pending_human_review` |
| staged rail build | `pass` |
| source art hash | `pass` |
| audio referenced only | `pass` |
| caption/transcript copied | `pass_no_copy` |
| MP4/MOV created | `false` |
| downstream gates | `false` |

## Human Review Options

Please reply with exactly one disposition for this crew-liveliness full-runtime HTML rough proof: `keep`, `tighten`, or `reject`.

If kept, the next artifact can be a full-runtime MP4 render review packet only if explicitly authorized later.

## Sprite Overlay Reject Record

Disposition recorded: `reject`.

Reason: ghosted duplicate humans/background artifacts make the sprite overlay the wrong approach.

Next review artifact: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z`
