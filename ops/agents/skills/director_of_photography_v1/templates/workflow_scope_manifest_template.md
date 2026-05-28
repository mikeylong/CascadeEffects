# Workflow Scope Manifest Template

## Manifest

- `stage`: `workflow scope manifest`
- `episode_id`:
- `short_id`:
- `restart_name`: `challenger_first_production_restart`
- `scope_manifest_id`:
- `created_at`:
- `dp_owner`:
- `archival_motion_in_scope`: `true|false`
- `archival_role`: `none|reference_only|hybrid`
- `archival_hygiene_rule`: `none|strict clean`
- `archival_analog_look`: `none|selective`
- `archival_source_breadth`: `none|1-3 primary archival videos plus small backup set`
- `coordinator_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md`
- `dp_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/SKILL.md`
- `disposition`: `keep|tighten|diagnostic only|reject`
- `dp_approved`: `true|false`

## Active Roots

- `episode_short_root`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/<new_challenger_short_id>/`
- `episode_production_root`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/<new_challenger_short_id>/production/`
- `viz_short_root`: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/shorts/<new_challenger_short_id>/`

## Whitelisted Source And Audio Inputs

- `source_writer_packet_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/writer_packet.md`
- `source_longform_script_path`:
- `longform_fact_check_report_path`:
- `short_script_source_path`:
- `short_audio_package_path`:
- `short_audio_wav_path`:
- `short_audio_transcript_path`:
- `audio_package_sha256`:
- `packaged_audio_sha256`:
- `transcript_sha256`:

## DP-Approved Imports

Every import must be an exact file path. Directory imports are not allowed.

| import_id | exact_path | source_class | source_url_or_origin | reason | allowed_use | imported_by | imported_at |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | `legacy_reference|prior_render|research_source|audio_provenance|source_provenance|archival_motion_source` |  |  |  |  |  |

## Blocked By Default

- `/archive/`
- `/archives/`
- `/experiments/`
- `/legacy/`
- `/retired/`
- `/midjourney/`
- `/proof_stills/`
- diagnostic outputs
- mixed-review outputs
- old renders
- old manifests
- old casebook or keeper-derived constraints
- old model experiment rules
- episode constraints from Challenger, Hyatt, Therac, or 737 unless entered in the active constraint ledger

## Hydration Rules

- Active context may read only active roots, exact whitelisted source/audio inputs, and exact DP-approved imports.
- Visual research must not browse old folders to look for useful material.
- If archival motion is in scope, every active archival video import must carry both an exact local media path and the original source URL or origin note.
- If useful legacy material is found, stop and request DP import approval before using it.
- The manifest must be reviewed before DP research brief, visual research packet, still prompts, still renders, or motion renders.

## Handoff

- `may_begin_archival_footage_review`: `true|false`
- `may_begin_visual_research`: `true|false`
- `blockers`:
- `next_action`:
