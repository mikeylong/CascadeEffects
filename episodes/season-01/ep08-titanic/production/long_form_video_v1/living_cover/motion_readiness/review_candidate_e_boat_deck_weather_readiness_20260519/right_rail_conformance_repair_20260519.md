# Titanic Right Rail Conformance Repair

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Artifact: `review.html`

Scope: motion-readiness HTML style repair only. Candidate E source art, caption sample text, ambient/effects intent, audio state, rough assembly lock, final render lock, upload lock, YouTube lock, and public release lock are unchanged.

## Repair Summary

The active Titanic motion-readiness review surface was tightened to match `fixed_16x9_right_rail_v1` and the current Tacoma-style Living Cover rail implementation.

Changes made:

- Right rail now uses fixed right-side geometry: `right: 52px`, `top: 52px`, `bottom: 52px`, `width: 760px`, `grid-template-rows: auto minmax(0, 1fr) auto`, and `gap: 28px`.
- Rail classes now use shared Living Cover vocabulary: `active-panel`, `eyebrow`, `active-title`, `active-summary`, `context-list`, `context-row`, `context-dot`, `rail-caption`, and `caption-softener`.
- Caption treatment is no longer a rounded lower card. It uses a separate lower-right localized softener and plain native rail caption text.
- Active panel keeps the canonical `8px` radius and `34px 36px 36px` padding, with source-aware cold blue-gray panel fill.
- Context dots are flat muted `8px` markers with no warm glow.
- Right rail display copy suppresses terminal periods for title, context, and rail-caption sample text. `active-summary` may use sentence punctuation.
- No new out-of-rail viewer-facing text, diagnostic label, Paper Architecture treatment, admin prop, or cue-map overlay was added.

## Conformance Reads

- `right_rail_safe_space_read`: `pass_fixed_right_52_top_bottom_52_width_760`
- `rail_typography_conformance_read`: `pass_fixed_26_64_34_28_40_px_hierarchy`
- `rail_shared_vocabulary_read`: `pass_tacoma_style_living_cover_classes`
- `caption_softener_scope_read`: `pass_separate_lower_rail_softener_no_card_badge_border_or_glow`
- `localized_readability_treatment_read`: `pass_active_panel_and_separate_caption_softener_only`
- `right_rail_opacity_balance_read`: `pass_no_full_height_opaque_right_column`
- `context_region_source_visibility_read`: `pass_context_region_has_no_opaque_backing`
- `rail_punctuation_style_read`: `pass_no_terminal_periods_except_active_summary`
- `viewer_text_surface_inventory_read`: `pass_right_rail_chapter_context_caption_only`
- `out_of_rail_text_read`: `pass_no_viewer_facing_out_of_rail_text_inside_canvas`

## Validation Note

Static HTML/CSS checks confirmed the repaired selectors and removed the prior rounded caption card class. In-app browser automation refused to reload or inspect the local `file://` review page under Browser URL policy, so no new browser-driven screenshots were generated in this repair pass. Existing screenshot files remain path/hash-valid historical motion-readiness references, but the conformance evidence for this repair is the repaired HTML plus this static rail-conformance note.

## Gate Boundary

Current gate remains `motion_readiness_keep`.

Next required gate remains `human_motion_readiness_keep_or_tighten_reject`.

Rough assembly, final render, upload prep, YouTube action, and public release remain blocked.
