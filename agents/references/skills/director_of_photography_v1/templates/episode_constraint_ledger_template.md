# Episode Constraint Ledger Template

## Ledger

- `stage`: `episode constraint ledger`
- `episode_id`:
- `short_id`:
- `workflow_scope_manifest_path`:
- `dp_research_brief_path`:
- `narration_map_path`:
- `visual_research_packet_path`:
- `visual_beatmap_path`:
- `dp_shot_packet_path`:
- `archival_footage_review_path`: `pending unless archival motion is in scope`
- `dp_owner`:
- `approved_at`:
- `archival_role`: `none|reference_only|hybrid`
- `archival_hygiene_rule`: `none|strict clean`
- `archival_analog_look`: `none|selective`
- `archival_source_breadth`: `none|1-3 primary archival videos plus up to 2 backups`
- `historical_signal_texture_registry_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json`
- `historical_signal_texture_policy`: `none|house_crt_default`
- `historical_context_year_or_range`:
- `default_historical_signal_profile_id`: `none|era_1980s_broadcast_crt_v1`
- `inter_clip_static_policy`: `none|randomized_tv_static_between_story_clips`
- `ledger_status`: `draft|active|superseded|retired`
- `disposition`: `keep|tighten|diagnostic only|reject`
- `dp_approved`: `true|false`

## Constraint Classes

Use these classes when auditing or approving constraints.

- `active`: controls the current scoped short now.
- `conditional`: may activate only when the named condition is met.
- `legacy_reference`: retained only for context; not allowed to control generation.
- `retired`: explicitly rejected for this restart.

## Active Constraints

Every active constraint needs evidence and a scope. Do not promote a rule because it appeared in an old prompt, casebook, model experiment, keeper registry, or previous episode.

| constraint_id | status | applies_to | constraint | evidence_paths_or_urls | owner | activation_condition | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | `active|conditional|legacy_reference|retired` | `episode|short|beat|shot|model|prompt|motion|final_export` |  |  | `DP` |  |  |

## Legacy Constraint Audit

| source_path_or_rule | prior_episode_or_experiment | proposed_status | reason | DP_decision |
| --- | --- | --- | --- | --- |
|  | `Challenger|Hyatt|Therac|737|casebook|keeper_registry|model_experiment|style_package` | `legacy_reference|retired|conditional|active` |  |  |

## Research-To-Constraint Trace

| evidence_id | evidence_path_or_url | beat_or_shot_id | constraint_ids_supported | gaps |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Change Log

| changed_at | changed_by | change | reason | affected_stages |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Handoff

- `may_enter_stills_contact_sheet`: `true|false`
- `coverage_selection_gate_ready`: `true|false`
- `hygiene_gate_ready`: `true|false`
- `blocked_until`:
- `blockers`:
- `next_action`:
