# Production Model Decision Template

Use this after the visual research packet and before the visual beatmap. Keep it short: this is a lane decision, not another research packet.

## Decision

- `stage`: `production model decision`
- `episode_id`:
- `short_id`:
- `visual_research_packet_path`:
- `archival_footage_review_path`: `pending unless archival motion is in scope`
- `workflow_scope_manifest_path`:
- `dp_research_brief_path`:
- `decision_owner`: `coordinator`
- `dp_reviewed`: `true|false`
- `production_model_lane`: `source_led_motion|source_derived_reanimation|sourced_stills|generated_stills|hybrid`
- `lane_rationale`: `why this is the cheapest viable path to an engaging Short`
- `generated_stills_policy`: `exception_only|expected|blocked`
- `source_first_read`: `pass|tighten|reject`
- `engagement_read`: `pass|tighten|reject`
- `disposition`: `keep|tighten|diagnostic only|reject`
- `may_lock_visual_beatmap`: `true|false`

## Hero Source Families

| `source_family_id` | `source_family_role` | `coverage_role` | `expected_screen_time_role` | `why_it_should_carry_attention` | `source_limitations` |
|---|---|---|---|---|---|
|  | `hero_event|mechanism_process|institutional_context|human_context|texture_reference` | `opening|middle|ending|support` | `dominant|brief_context|support_insert` |  |  |

## Lane Rules

- `room_admin_process_budget`: `max seconds or max shots when relevant`
- `subject_event_over_literal_coverage`: `where hero subject/event imagery should beat literal narration mapping`
- `source_derived_reanimation_expected`: `true|false`
- `direct_source_clip_expected`: `true|false`
- `sourced_stills_expected`: `true|false`
- `generated_stills_allowed_only_when`: `state exact exception rule`
- `known_bad_lanes`: `lanes to avoid because they caused drift, weak visuals, or wasted renders`

## Render Authorization Defaults

- `default_render_authorization_read`: `pass|tighten|reject`
- `source_clip_or_still_solves_first`: `true|false`
- `source_derived_reanimation_before_generated_stills`: `true|false`
- `generated_still_requires_reason`: `true`

## Handoff

- `next_required_stage`: `visual beatmap|visual research packet`
- `blockers`:
- `deferred_gaps`:
- `may_advance`: `true|false`
