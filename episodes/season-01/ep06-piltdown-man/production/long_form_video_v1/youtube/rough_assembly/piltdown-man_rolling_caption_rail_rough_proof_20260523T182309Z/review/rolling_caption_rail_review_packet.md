# Piltdown Man Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `piltdown-man`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown-man_rolling_caption_rail_rough_proof_20260523T182309Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown-man_rolling_caption_rail_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `none`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`
- Caption display chunking: `script_locked_chunk_split_v1`
- Review chrome policy: `hidden_in_render_mode`
- Highlight render policy: `reviewed_cue_map_spans_only`
- Caption motion model: `constant_speed_audio_time_aligned_scroll_v2`
- Caption timeline layout: `audio_time_positioned_stack_v1`
- Caption sync target: `pre_vo_reading_lead_active_band_v1`
- Caption reading lead: `0.65s`
- Caption speed scope: `per_episode_constant_px_per_second`
- Caption window treatment: `transparent_caption_mask_only_v1`
- Caption opacity model: `viewport_distance_smoothstep_v1`
- Highlight phrase scope: `exact_authored_span_only`
- Caption highlight model: `lesson_takeaway_highlight_v1`
- Highlight semantic role: `story_lesson_takeaway`
- Highlight density model: `memorable_takeaway_cadence_v1`
- Highlight color model: `source_sampled_backplate_contrast_takeaway_accent_v3`
- Highlight visual timing model: `active_band_presence_aligned_v1`
- Caption collision guard: `fixed_line_box_visual_gap_guard_v1`


## Gate Handling

- Action: `pause_final_assembly_create_successor_rough_proof_from_kept_rough`
- Status: `rolling_caption_rail_final_assembly_paused_successor_rough_assembly_review_ready_pending_human_keep`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human `keep`.


## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The proof is injected into the predecessor rough proof shell so the kept source art, ambient behavior, audio timing, and end-screen timing remain active.
- The caption window has no blur, fill, panel, or container background; readability relies on source-aware text color, text shadow, and the entry/exit mask.
- Old previous/upcoming context rows are absent.
- Highlights render only from cue-map spans that are authored as story lesson/takeaway phrases, not technical labels or isolated single words.
- At the end-screen transition, captions continue upward and caption text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Spans

- precisely the kind of evolutionary missing link (26.997 to 34.285s): #efef9f; human_approved_lesson_takeaway_span_20260523
- accepted for forty-one years (59.292 to 67.488s): #efef9f; human_approved_lesson_takeaway_span_20260523
- not because the evidence was strong (108.351 to 111.436s): #efef9f; human_approved_lesson_takeaway_span_20260523
- already prepared to believe (114.581 to 117.625s): #efef9f; human_approved_lesson_takeaway_span_20260523
- fit this model precisely (182.136 to 184.699s): #efef9f; human_approved_lesson_takeaway_span_20260523
- cost of the alternative was high (268.421 to 270.344s): #efef9f; human_approved_lesson_takeaway_span_20260523
- exactly what was needed (348.685 to 353.11s): #efef9f; human_approved_lesson_takeaway_span_20260523
- taken as evidence that it was real (350.727 to 357.535s): #efef9f; human_approved_lesson_takeaway_span_20260523
- social cost of sustained public skepticism (386.448 to 392.679s): #efef9f; human_approved_lesson_takeaway_span_20260523
- pattern of inconsistencies was never assembled (457.316 to 463.323s): #efef9f; human_approved_lesson_takeaway_span_20260523
- story outran the quality of the evidence (464.104 to 468.95s): #efef9f; human_approved_lesson_takeaway_span_20260523
- provenance was not independently controlled (479.181 to 482.345s): #efef9f; human_approved_lesson_takeaway_span_20260523
- evidentiary basis had become almost invisible (530.2 to 537.41s): #efef9f; human_approved_lesson_takeaway_span_20260523
- systematic analysis using microscopy (555.153 to 563.751s): #efef9f; human_approved_lesson_takeaway_span_20260523
- institutional will to demand investigation (586.142 to 593.091s): #efef9f; human_approved_lesson_takeaway_span_20260523
- forger is less significant than the question (626.386 to 631.571s): #efef9f; human_approved_lesson_takeaway_span_20260523
- already disposed to accept it (653.475 to 659.059s): #efef9f; human_approved_lesson_takeaway_span_20260523
- right credentials, at the right moment (724.388 to 729.446s): #efef9f; human_approved_lesson_takeaway_span_20260523
- lenses were not designed to ask (737.38 to 739.784s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Forty-one years is not evidence of stupidity (743.972 to 748.7s): #efef9f; human_approved_lesson_takeaway_span_20260523
- institutional belief can do (748.933 to 753.66s): #efef9f; human_approved_lesson_takeaway_span_20260523
- evidence was too good to be true (829.291 to 830.913s): #efef9f; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
