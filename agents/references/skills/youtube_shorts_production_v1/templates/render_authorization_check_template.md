# Render Authorization Check Template

Use this after `shot_plan_v2` and active ledger approval, before still or motion generation. This is a blocker gate that prevents unnecessary generation.

## Authorization

- `stage`: `render authorization check`
- `episode_id`:
- `short_id`:
- `production_model_decision_path`:
- `production_model_lane`: `source_led_motion|source_derived_reanimation|sourced_stills|generated_stills|hybrid`
- `shot_plan_v2_path`:
- `episode_constraint_ledger_path`:
- `visual_research_packet_path`:
- `archival_footage_review_path`: `pending unless archival motion is in scope`
- `render_authorization_read`: `pass|tighten|reject`
- `disposition`: `keep|tighten|diagnostic only|reject`
- `may_start_stills_or_motion_generation`: `true|false`

## Shot Decisions

| `shot_id` | `visual_beat_id` | `approved_source_solves` | `authorized_lane` | `source_or_generation_reason` | `render_authorization_read` |
|---|---|---|---|---|---|
|  |  | `true|false` | `sourced_clip_or_still|source_derived_reanimation|generated_still|hybrid` |  | `pass|tighten|reject` |

## Block Rules

- `generated_still_blocked_when_source_solves`: `true`
- `source_derived_reanimation_preferred_when_source_motion_is_strong`: `true`
- `requires_dp_override_for_generation`: `true when production_model_lane is source_led_motion or source_derived_reanimation`

## Handoff

- `shots_authorized_for_sourced_clip_or_still`:
- `shots_authorized_for_source_derived_reanimation`:
- `shots_authorized_for_generated_still`:
- `blockers`:
- `next_required_stage`:
