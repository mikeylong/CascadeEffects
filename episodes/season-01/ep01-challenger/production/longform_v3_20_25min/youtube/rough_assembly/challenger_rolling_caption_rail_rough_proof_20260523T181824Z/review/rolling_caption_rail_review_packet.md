# Challenger Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `challenger`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T181824Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T181824Z/rough_assembly_manifest.json`
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

- Action: `supersede_publish_final_surfaces_create_successor_rough_proof`
- Status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`
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

- the first warning appeared (3.632 to 8.479s): #efef9f; human_approved_lesson_takeaway_span_20260523
- warning stay visible in records (70.373 to 73.506s): #efef9f; human_approved_lesson_takeaway_span_20260523
- failed after a system learned (84.254 to 87.585s): #efef9f; human_approved_lesson_takeaway_span_20260523
- A scrub is still an engineering decision (124.703 to 127.73s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Normal operation is useful (161.894 to 165.822s): #efef9f; human_approved_lesson_takeaway_span_20260523
- inside a decision structure (188.868 to 192.331s): #efef9f; human_approved_lesson_takeaway_span_20260523
- the practical standard drifted (264.882 to 269.06s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Timing was the safety margin (335.925 to 338.026s): #efef9f; human_approved_lesson_takeaway_span_20260523
- warning can die inside a large organization (414.91 to 419.841s): #efef9f; human_approved_lesson_takeaway_span_20260523
- answer depends on the question (459.021 to 462.639s): #efef9f; human_approved_lesson_takeaway_span_20260523
- first question keeps the schedule alive (480.355 to 482.62s): #efef9f; human_approved_lesson_takeaway_span_20260523
- judgment becomes a schedule decision (483.562 to 487.747s): #efef9f; human_approved_lesson_takeaway_span_20260523
- decision becomes precedent (502.083 to 505.606s): #efef9f; human_approved_lesson_takeaway_span_20260523
- previous success can become misleading evidence (578.533 to 581.119s): #efef9f; human_approved_lesson_takeaway_span_20260523
- survival as part of the safety case (603.379 to 608.083s): #efef9f; human_approved_lesson_takeaway_span_20260523
- reversed the burden of proof (687.911 to 689.851s): #efef9f; human_approved_lesson_takeaway_span_20260523
- absence became useful to the launch case (716.501 to 721.294s): #efef9f; human_approved_lesson_takeaway_span_20260523
- A warning also has to travel (775.186 to 777.849s): #efef9f; human_approved_lesson_takeaway_span_20260523
- system has made a decision without naming it (798.515 to 803.753s): #efef9f; human_approved_lesson_takeaway_span_20260523
- warning arrive too late (824.666 to 827.655s): #efef9f; human_approved_lesson_takeaway_span_20260523
- explanation arrived, and flight continued (899.926 to 905.552s): #efef9f; human_approved_lesson_takeaway_span_20260523
- evidence already existed (945.148 to 947.692s): #efef9f; human_approved_lesson_takeaway_span_20260523
- received a softened version (1001.986 to 1007.491s): #efef9f; human_approved_lesson_takeaway_span_20260523
- expected performance becomes normal (1016.521 to 1023.197s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Missing data gets mistaken for safety (1061.494 to 1063.555s): #efef9f; human_approved_lesson_takeaway_span_20260523
- proof standards quietly (1071.032 to 1076.851s): #efef9f; human_approved_lesson_takeaway_span_20260523
- certainty of disaster justifies delay (1082.913 to 1085.85s): #efef9f; human_approved_lesson_takeaway_span_20260523
- warning is strong enough to interrupt momentum (1129.535 to 1132.308s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Disasters rarely begin at the moment of impact (1133.29 to 1140.522s): #efef9f; human_approved_lesson_takeaway_span_20260523
- stopped to understand (1144.9 to 1147.793s): #efef9f; human_approved_lesson_takeaway_span_20260523
- The system explained it (1173.053 to 1179.219s): #efef9f; human_approved_lesson_takeaway_span_20260523
- what it already knew (1181.398 to 1182.898s): #efef9f; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
