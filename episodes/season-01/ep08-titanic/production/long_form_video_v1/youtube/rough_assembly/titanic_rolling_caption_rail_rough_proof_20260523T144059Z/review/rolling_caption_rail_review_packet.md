# Titanic Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `titanic`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_rolling_caption_rail_rough_proof_20260523T144059Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_rolling_caption_rail_rough_proof_20260523T144059Z/rough_assembly_manifest.json`
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

- law was measuring the wrong thing (48.173 to 54.221s): #dede35; human_approved_lesson_takeaway_span_20260523
- They began with a category (59.128 to 62.011s): #dede35; human_approved_lesson_takeaway_span_20260523
- Titanic was far beyond the world (90.371 to 93.977s): #dede35; human_approved_lesson_takeaway_span_20260523
- the world changes around it (137.788 to 143.395s): #dede35; human_approved_lesson_takeaway_span_20260523
- table had stopped tracking the scale (163.078 to 165s): #dede35; human_approved_lesson_takeaway_span_20260523
- law did not say, count the people (197.251 to 200.655s): #dede35; human_approved_lesson_takeaway_span_20260523
- old rule had a simpler answer ready (263.693 to 268.661s): #dede35; human_approved_lesson_takeaway_span_20260523
- minimum into a signal of adequacy (316.093 to 321.8s): #dede35; human_approved_lesson_takeaway_span_20260523
- rulebook was the smaller imagination (360.025 to 363.531s): #dede35; human_approved_lesson_takeaway_span_20260523
- safety system would have had to think (394.909 to 400.554s): #dede35; human_approved_lesson_takeaway_span_20260523
- reduced that system to a table (405.879 to 411.951s): #dede35; human_approved_lesson_takeaway_span_20260523
- smaller version of the risk (443.951 to 445.994s): #dede35; human_approved_lesson_takeaway_span_20260523
- law had turned scale into a category (511.454 to 517.829s): #dede35; human_approved_lesson_takeaway_span_20260523
- A mature safety system does not pick (561.893 to 568.24s): #dede35; human_approved_lesson_takeaway_span_20260523
- Then the proof arrives all at once (611.548 to 613.651s): #dede35; human_approved_lesson_takeaway_span_20260523
- question was no longer just (656.445 to 661.593s): #dede35; human_approved_lesson_takeaway_span_20260523
- failure was already present in the table (692.711 to 694.693s): #dede35; human_approved_lesson_takeaway_span_20260523
- category built for yesterday's ship (699.72 to 702.643s): #dede35; human_approved_lesson_takeaway_span_20260523
- law had stopped measuring the ships (710.29 to 713.192s): #dede35; human_approved_lesson_takeaway_span_20260523
- reality audits the system (726.864 to 728.67s): #dede35; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
