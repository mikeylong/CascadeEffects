# Therac-25 Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `therac-25`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260522T223902Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json`
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

- She says something went wrong (42.477 to 43.738s): #c7282a; human_approved_lesson_takeaway_span_20260523
- system earns trust it was never tested (60.554 to 66.44s): #c7282a; human_approved_lesson_takeaway_span_20260523
- The machine exists to hold that margin (92.87 to 95.975s): #c7282a; human_approved_lesson_takeaway_span_20260523
- machine must not fire (151.432 to 154.396s): #c7282a; human_approved_lesson_takeaway_span_20260523
- patient would still be safe (201.621 to 210.818s): #c7282a; human_approved_lesson_takeaway_span_20260523
- code was already proven (226.005 to 232.512s): #c7282a; human_approved_lesson_takeaway_span_20260523
- never been tested operating alone (233.193 to 239.56s): #c7282a; human_approved_lesson_takeaway_span_20260523
- treated as proof that no problem existed (248.771 to 256.539s): #c7282a; human_approved_lesson_takeaway_span_20260523
- safety net was removed (256.579 to 260.043s): #c7282a; human_approved_lesson_takeaway_span_20260523
- skip the safety check (319.907 to 322.292s): #c7282a; human_approved_lesson_takeaway_span_20260523
- machine earns trust it does not deserve (378.468 to 383.837s): #c7282a; human_approved_lesson_takeaway_span_20260523
- track record belonged to a different context (400.063 to 403.728s): #c7282a; human_approved_lesson_takeaway_span_20260523
- interface trained them to override warnings (480.923 to 483.164s): #c7282a; human_approved_lesson_takeaway_span_20260523
- the data won (509.953 to 512.838s): #c7282a; human_approved_lesson_takeaway_span_20260523
- safety that had never been stress-tested (537.442 to 544.71s): #c7282a; human_approved_lesson_takeaway_span_20260523
- safety systems made such an overdose impossible (595.975 to 603.484s): #c7282a; human_approved_lesson_takeaway_span_20260523
- machine was not responsible (619.654 to 622.377s): #c7282a; human_approved_lesson_takeaway_span_20260523
- machine was fundamentally sound (692.342 to 699.697s): #c7282a; human_approved_lesson_takeaway_span_20260523
- designed to confirm safety (767.011 to 770.737s): #c7282a; human_approved_lesson_takeaway_span_20260523
- failure to prove itself (788.054 to 794.379s): #c7282a; human_approved_lesson_takeaway_span_20260523
- no independent safety monitoring (799.463 to 802.666s): #c7282a; human_approved_lesson_takeaway_span_20260523
- not designed to communicate danger (820.756 to 823.539s): #c7282a; human_approved_lesson_takeaway_span_20260523
- software lived in a gap (866.433 to 869.177s): #c7282a; human_approved_lesson_takeaway_span_20260523
- designed to trust itself (895.334 to 898.719s): #c7282a; human_approved_lesson_takeaway_span_20260523
- safety layer is treated as simplification (920.384 to 923.768s): #c7282a; human_approved_lesson_takeaway_span_20260523
- trust in systems that are too complex (979.96 to 986.559s): #c7282a; human_approved_lesson_takeaway_span_20260523
- conditions where it could fail (1018.634 to 1024.561s): #c7282a; human_approved_lesson_takeaway_span_20260523
- trust is the kind that has never been tested (1032.277 to 1035.804s): #c7282a; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
