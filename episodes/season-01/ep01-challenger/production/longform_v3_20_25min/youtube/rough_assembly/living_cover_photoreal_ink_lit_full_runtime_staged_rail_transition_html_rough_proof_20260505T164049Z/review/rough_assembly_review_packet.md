# Challenger Living Cover Staged Rail Transition HTML Rough Review

Packet: `living_cover_photoreal_ink_lit_full_runtime_staged_rail_transition_html_rough_proof_20260505T164049Z`
Gate: `rough_assembly_gate`
Status: `review_ready_pending_human_staged_rail_transition_html_rough_keep`
Human disposition: `defer`

## What Changed

- Current clean-rail fast-transition HTML proof is recorded as `tighten`.
- The issue is transition sequencing: too many layout, typography, detail, and source-art changes happened at once.
- Compact chapter rows now keep stable slots.
- A separate active-detail layer carries the large title, summary, and current subbeat.
- The staged rail build keeps a `600ms` total crossover: outgoing detail settles, title/accent lands, then summary/subbeat appears.
- Animated layout reflow is removed for font size, max height, display, and active-card padding.
- The proof still covers the full `00:21:29.131` approved audio timeline with 8 major sections.
- YouTube-legible active text sizing and `window.__setRenderTime` are preserved.

## Player

- HTML proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_staged_rail_transition_html_rough_proof_20260505T164049Z/player.html`
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

Please reply with exactly one disposition for this staged-rail-transition full-runtime HTML rough proof: `keep`, `tighten`, or `reject`.

If kept, the next artifact can be a full-runtime MP4 render review packet only if explicitly authorized later.

## Crew Liveliness Tighten Record

Disposition recorded: `tighten` for crew liveliness.

Reviewer notes: staged rail is much better, but the astronauts still feel too static for a Living Cover. The next proof should add restrained foreground human motion while preserving all existing gates and locked actions.

Next review artifact: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_crew_liveliness_html_rough_proof_20260505T170441Z`
