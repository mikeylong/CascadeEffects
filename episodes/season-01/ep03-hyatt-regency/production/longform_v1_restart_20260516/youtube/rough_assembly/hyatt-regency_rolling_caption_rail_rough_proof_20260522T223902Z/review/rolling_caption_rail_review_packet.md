# Hyatt Regency Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `hyatt-regency`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260522T223902Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json`
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
- Highlight color model: `source_sampled_distinct_takeaway_accent_v2`
- Highlight visual timing model: `active_band_presence_aligned_v1`
- Caption collision guard: `fixed_line_box_visual_gap_guard_v1`

## Gate Handling

- Action: `supersede_publish_final_surfaces_create_successor_rough_proof`
- Status: `final_assembly_keep_recorded_mp4_render_gate_open_publish_readiness_pending`
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

- designed to feel like an occasion (26.2 to 29.885s): #e1180e; human_approved_lesson_takeaway_span_20260523
- lost the ability to recognize it (81.428 to 83.41s): #e1180e; human_approved_lesson_takeaway_span_20260523
- logic of that system is worth pausing (154.54 to 160.447s): #e1180e; human_approved_lesson_takeaway_span_20260523
- fabrication was inconvenient (213.038 to 216.447s): #e1180e; human_approved_lesson_takeaway_span_20260523
- looked like a minor adjustment (233.115 to 235.639s): #e1180e; human_approved_lesson_takeaway_span_20260523
- approved with no load recalculation (248.238 to 251.883s): #e1180e; human_approved_lesson_takeaway_span_20260523
- pass through the system unchecked (311.536 to 313.559s): #e1180e; human_approved_lesson_takeaway_span_20260523
- responsible for verifying the load path (350.337 to 355.243s): #e1180e; human_approved_lesson_takeaway_span_20260523
- fabrication convenience, not redesign (376.923 to 380.047s): #e1180e; human_approved_lesson_takeaway_span_20260523
- behavior of the system may have changed (394.712 to 398.838s): #e1180e; human_approved_lesson_takeaway_span_20260523
- does this change the load path (414.56 to 417.563s): #e1180e; human_approved_lesson_takeaway_span_20260523
- warning signs during construction did not trigger (476.479 to 485.129s): #e1180e; human_approved_lesson_takeaway_span_20260523
- signals about system-level weakness (508.238 to 515.015s): #e1180e; human_approved_lesson_takeaway_span_20260523
- best opportunity to find problems (528.259 to 535.231s): #e1180e; human_approved_lesson_takeaway_span_20260523
- already-deficient system into certainty (553.575 to 560.463s): #e1180e; human_approved_lesson_takeaway_span_20260523
- no single person had made a decision (592.621 to 598.287s): #e1180e; human_approved_lesson_takeaway_span_20260523
- process absorbed into a category labeled routine (620.313 to 627.122s): #e1180e; human_approved_lesson_takeaway_span_20260523
- why the system did not require one (663.157 to 669.425s): #e1180e; human_approved_lesson_takeaway_span_20260523
- changes the load path (666.402 to 669.425s): #e1180e; human_approved_lesson_takeaway_span_20260523
- category that does not require deep review (722.502 to 726.245s): #e1180e; human_approved_lesson_takeaway_span_20260523
- crossed a category boundary (790.789 to 793.655s): #e1180e; human_approved_lesson_takeaway_span_20260523
- system worked exactly as designed (825.518 to 828.186s): #e1180e; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
