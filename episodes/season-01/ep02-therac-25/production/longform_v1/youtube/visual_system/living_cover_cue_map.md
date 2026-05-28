# Therac-25 Living Cover Cue Map

- Cue map version: `living_cover_cue_map_v1`
- Gate: `visual_system_gate`
- Status: `review_ready`
- Human disposition: `defer`
- Source-art lane: `cascade-ink-lit-photoreal-v1`

## Cue Contract

The cue map turns the chapter spine into authored Living Cover behavior. It is an internal production artifact only: it must not render as a standalone cue card, cue panel, node list, label, or implementation-status surface. It keeps all cue behavior source-safe through chapter shifts, approved typography/caption/rail behavior, source-art opacity/transform, and end-screen timing only. No diagnostic connector lines, cyan signal traces, generated UI paths, or procedural marks are drawn over the photoreal source art.

## Episode Cues

1. `opening_contradiction`: Patient reports injury / console reports normal / trust chooses machine.
2. `beam_path_rule`: Mode selected / hardware moves / beam must match.
3. `safety_net_removed`: Inherited code / interlocks removed / software alone.
4. `eight_second_state`: Type / correct fast / wrong state.
5. `routine_error`: Cryptic code / retry allowed / warning fades.
6. `trust_layers`: Reputation / repetition / instrument over patient.
7. `pattern_repeats`: Georgia / Tyler / no shared picture.
8. `burden_reversed`: Report / cannot reproduce / case closed.
9. `software_grades_itself`: Control / judge / no watcher.
10. `trust_tested`: Track record / untested edge / false confidence.
11. `outro_next_pattern`: Next case / same pattern / known warning.

## Reads

- `living_cover_cue_map_read`: `pass`
- `chapter_cue_coverage_read`: `pass_all_major_chapters_have_source_safe_cues`
- `typography_cue_read`: `pass_key_phrase_typography_present`
- `effect_map_cue_read`: `pass_4_to_8_effect_map_moments`
- `source_safe_motion_read`: `pass_opacity_transform_rail_panel_only_no_source_art_diagnostic_marks`
- `cue_no_diagnostic_overlay_read`: `pass_no_cyan_lines_connector_paths_or_generated_ui_over_source_art`
- `cue_map_internal_artifact_read`: `pass_internal_only_not_rendered`
- `visible_cue_overlay_read`: `pass_no_visible_cue_panel_card_label_or_node_list`
