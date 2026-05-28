# Shot Timing EDL Template

Use this before `motion video proof`. This is the proof-edit authority; beat rows and five-second handles are source metadata only.

## EDL

- `stage`: `shot_timing_edl`
- `episode_id`:
- `short_id`:
- `production_model_decision_path`:
- `motion_contact_sheet_manifest_path`:
- `approved_audio_path`:
- `approved_audio_duration_seconds`:
- `story_shot_duration_floor_seconds`: `2.0`
- `contact_sheet_to_proof_parity_read`: `pass|tighten|reject`
- `hidden_cut_read`: `pass|tighten|reject`
- `story_shot_duration_read`: `pass|tighten|reject`
- `disposition`: `keep|tighten|diagnostic only|reject`
- `may_start_motion_video_proof`: `true|false`

## Story Shots

| `shot_id` | `covered_beat_ids` | `source_path` | `source_span_in` | `source_span_out` | `intended_duration_seconds` | `actual_duration_seconds` | `continuity_vector` | `no_internal_cut_read` |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  | `pass|tighten|reject` |

## Continuity Checks

- `no_unlisted_source_native_cuts`: `true|false`
- `no_sub_floor_story_flashes`: `true|false`
- `proof_order_matches_contact_sheet_selection`: `true|false`
- `beat_rollup_used_only_as_secondary_view`: `true`
- `blockers`:
