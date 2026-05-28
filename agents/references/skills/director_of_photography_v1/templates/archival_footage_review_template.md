# Archival Footage Review Template

## Review Packet

- `stage`: `archival footage review`
- `episode_id`:
- `short_id`:
- `workflow_scope_manifest_path`:
- `dp_research_brief_path`:
- `narration_map_path`:
- `visual_research_packet_path`: `pending until the archival review informs the packet`
- `dp_owner`:
- `archival_role`: `hybrid`
- `hygiene_rule`: `strict clean`
- `analog_look`: `selective`
- `source_breadth`: `1-3 primary archival videos plus up to 2 backups`
- `seed_source_url`:
- `disposition`: `keep|tighten|diagnostic only|reject`
- `blockers`:

## Source Pool

- `primary_source_ids`:
- `backup_source_ids`:
- `primary_source_limit`: `3`
- `backup_source_limit`: `2`
- `active_primary_source_count`:
- `active_backup_source_count`:
- `source_pool_within_limit`: `true|false`

## Hygiene Rules

- Any visible logo, stinger, lower-third, watermark, burned-in caption, end card, split screen, or channel bug is an automatic `reject`.
- No crop, cleanup, inpaint, or prompt-level “ignore the logo” fallback is allowed in this pass.
- Active sourced or hybrid archival use requires an exact local media path plus the original source URL or origin note.
- `texture_profile: broadcast_1986|vhs_1986` may be used only on beats tied to an approved archival footage family.

## Sources

### `source_id`

- `source_url`:
- `local_media_path`:
- `source_title`:
- `source_channel_or_origin`:
- `source_provenance_note`:
- `source_family`:
- `source_role`: `primary|backup`
- `source_hygiene_summary`:
- `source_notes`:

#### Clip Review

| clip_id | timecode_in | timecode_out | clip_role | visual_strength_score | mechanism_relevance_score | motion_reference_score | reanimation_suitability_score | hygiene_status | hygiene_failures | clean_span_confirmed | same_camera_span_confirmed | selected_for_visual_beat_ids | texture_profile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | `reference_only|sourced_candidate|texture_reference|reanimation_candidate` | `1-5` | `1-5` | `1-5` | `1-5` | `pass|reject` |  | `true|false` | `true|false` |  | `none|broadcast_1986|vhs_1986` |

#### Reanimation Keyframe Candidates

| keyframe_pair_id | clip_id | start_timecode | end_timecode | start_keyframe_path | end_keyframe_path | same_camera_span_confirmed | crop_consistency_read | recommended_motion_strategy | reanimation_rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | `true|false` | `pass|tighten|reject` | `direct_source_clip|source_derived_reanimation|still_driven_i2v` |  |

## Teaching-Pass Notes

- `multiple_narration_lines_may_share_one_footage_family`: `true`
- `technical_insert_cap`: `1 insert-heavy beat family or 2 insert shots total unless DP override is recorded`
- `literal_evidence_coverage_is_support_only`: `true`
- `engaging_clean_spans_prioritized_first`: `true`
- `source_derived_reanimation_prioritized_when_source_motion_has_best_visual_language`: `true`
- `generated_stills_exception_only_when_source_motion_or_frames_do_not_solve_the_shot`: `true`

## Handoff

- `may_inform_visual_research_packet`: `true|false`
- `may_lock_visual_beatmap`: `true|false`
- `hygiene_pass_clip_total`:
- `selected_primary_footage_families`:
- `next_action`:
