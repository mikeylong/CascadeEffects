# Titanic Source-Art Generation Review Packet

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `source_art_keep`

Disposition: `review_ready_pending_human_keep`

## Candidate

- Candidate ID: `candidate_a_boat_deck_regulation_gap`
- Source-art lane: `cascade-ink-lit-photoreal-v1`
- Episode visual style: `titanic_boat_deck_lifeboat_regulation_gap_photoreal_v1`
- Generation tool: `codex_builtin_image_gen`
- Model: `unknown_builtin_image_gen_model`
- Model confidence: `inferred_from_path`
- Built-in source image: `/Users/mike/.codex/generated_images/019e3c20-86fc-7261-82b9-8842ab1cf076/ig_07220dc0fc2d5ef3016a0bf1890d7c8196afd377e1313b2ee6.png`
- Built-in source image SHA-256: `fae8c0d6bf7e4260dde90a81765b7f4c1ed8b46c2d616e14d1958aa392f0aa92`
- Raw workspace copy: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_a_boat_deck_regulation_gap_raw.png`
- Raw workspace SHA-256: `fae8c0d6bf7e4260dde90a81765b7f4c1ed8b46c2d616e14d1958aa392f0aa92`
- Normalized 1920x1080 source-art plate: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_a_boat_deck_regulation_gap_1920x1080.png`
- Normalized source-art SHA-256: `2fe42d7124606ce57559e6f84af070701fed3f322ac0e4b51918ecfd694e64ae`
- Prompt: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/prompts/titanic_source_art_imagegen_non_paper_prompt_20260519.md`
- Prompt SHA-256: `79d55ecca14fa17c273dd90544a0548a9640cb591f033c6b260e64f66d5fb899`

## QA Previews

- 960x540: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/qa/candidate_a_960x540.png`
- 960x540 SHA-256: `7fa69a48b09a25cc39fa4c9b03abb0451e0746ed80c4821a33af770b098aec81`
- 320x180: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/qa/candidate_a_320x180.png`
- 320x180 SHA-256: `2b6e2fc87cbe7dc6ab24119da53c07d16d5e4fa5ecb46b8ca394c4175d547cf7`
- 168x94: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/qa/candidate_a_168x94.png`
- 168x94 SHA-256: `742ded1463624b2edd7ca6dee6210d84f9f340ed919c66667215573b3e1bfcad`

## Review Reads

| Read | Status | Notes |
| --- | --- | --- |
| `historical_accuracy_read` | `pass_for_review` | Reads as an early-1910s ocean-liner boat deck with period lifeboats, davits, railings, deck lamps, and teak deck. |
| `source_reference_alignment_read` | `pass_for_review` | Aligns with the source-pull visual target: lifeboat/davit capacity and inspection/regulation context before the disaster. |
| `public_anchor_geometry_read` | `pass_for_review` | Large lifeboats, davits, rail, deck, and ocean horizon make the public scene legible. |
| `titanic_boat_deck_read` | `pass_for_review` | Boat-deck composition is clear without relying on ship-name text. |
| `lifeboat_davit_accuracy_read` | `pass_for_review` | Davit and lifeboat relationship is central and readable. |
| `lifeboat_capacity_visual_logic_read` | `pass_for_review` | Repeating davits/lifeboats plus open deck/sea space support the regulation-capacity visual hinge. |
| `board_of_trade_document_cue_read` | `pass_for_review` | Foreground ledger/inspection object is present with no readable text. |
| `period_maritime_materials_read` | `pass_for_review` | Wood, brass, riveted steel, lamps, and canvas/boat materials read period-appropriate. |
| `disaster_spectacle_absence_read` | `pass` | No sinking ship, iceberg, panic crowd, bodies, wreckage, fire, or collision spectacle. |
| `generated_text_logo_read` | `pass` | No readable text, ship-name lettering, logo, watermark, or title text observed. |
| `human_presence_read` | `pass` | One distant crew/inspector silhouette gives scale and institutional role. |
| `no_recognizable_faces_read` | `pass` | Human figure is back-turned and non-identifiable. |
| `texture_noise_read` | `pass_for_review` | Clean photoreal surface with no high-frequency speckle/grit/sandy texture at QA preview sizes. |
| `video_visual_style_scope_read` | `pass` | Non-Paper photoreal/source-preserving long-form video lane. |
| `paper_architecture_visual_style_read` | `pass_no_resemblance` | No folded-paper, foam-core, craft model, or Paper Architecture style. |
| `procedural_signal_overlay_read` | `pass` | No cyan connector lines, route overlays, UI paths, or diagnostic traces. |
| `ambient_line_artifact_read` | `pass` | No accidental line-art or overlay artifact observed. |
| `source_provenance_read` | `pass` | Built-in ImageGen source path, workspace copy, normalized plate, prompt, and hashes recorded. |
| `rights_and_content_id_risk_read` | `pass_low_generated_asset_risk` | Generated raster source-art candidate; still requires final package rights review later. |

## Review Notes

This candidate is suitable for human source-art review. It preserves the approved non-Paper long-form lane and avoids the main blockers: disaster spectacle, readable text, logo/ship-name dependence, Paper Architecture resemblance, and diagnostic overlays.

Open review consideration: the right-side rail safe area is ocean and sky, which should be usable for `fixed_16x9_right_rail_v1`; later proof work still needs a source-aware rail palette and localized readability treatment.

## Gate Effect

- Source-art candidate generated: `true`
- Source-art keep: `blocked_pending_human_keep`
- Cue map: `blocked`
- Ambient/effects layer: `blocked`
- Music integration contract: `blocked`
- Motion readiness: `blocked`
- Rough assembly: `blocked`
- Final MP4: `blocked`
- YouTube action: `blocked`
- Public release: `blocked`

## Review Ask

Review `candidate_a_boat_deck_regulation_gap`, then choose one:

- `keep source art`
- `tighten source art` with exact notes
- `reject source art` with exact notes
