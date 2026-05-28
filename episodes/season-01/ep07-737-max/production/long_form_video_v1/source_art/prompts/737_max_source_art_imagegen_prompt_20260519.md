# 737 MAX Source-Art ImageGen Prompt

- episode: 737 MAX
- workflow: long_form_video_production_v1
- stage: source_art_generation
- prompt_id: 737_max_living_cover_source_art_candidate_a_20260519
- visual_system_keep_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_visual_system_keep_20260519.md
- visual_system_keep_sha256: 1ceba16ef9d36b75b77c9e065eb5504a8e1c75042f9d7d85d7e273258155504b
- generation_tool: codex_builtin_image_gen
- target_canvas: 1920x1080
- output_role: long-form Living Cover generated raster source-art candidate
- candidate_status: invalidated_wrong_longform_style_paper_architecture
- video_visual_style_scope_read: reject_video_asset_used_paper_architecture
- paper_architecture_visual_style_read: reject
- long_form_source_art_lane_read: reject_paper_architecture_not_allowed_for_long_form_backplate
- paper_architecture_resemblance_read: reject

## Invalidation

This prompt is no longer active and must not be used for generation. It asked for Paper Architecture visual style in a long-form episode backplate. The 737 MAX visual-system gate must return to a non-Paper-Architecture long-form source-art lane before ImageGen source-art generation can reopen.

## Prompt

Use case: stylized-concept

Asset type: 1920x1080 long-form Living Cover source-art backplate candidate for Cascade Effects.

Primary request: Create an ink-lit Paper Architecture scene of the 737 MAX mechanism: a familiar aircraft whose changed engine/airframe relationship is being quietly corrected by a hidden software path.

Scene/backdrop: Deep ink-blue editorial field with warm cream folded-paper aircraft forms, muted lavender shadows, foam-core cut edges, translucent vellum, restrained coral warning accent, and controlled model-aircraft lighting.

Subject: An unbranded Boeing 737 MAX-family aircraft nose and enlarged forward/high-mounted LEAP engine profile, shown as a clean folded-paper fuselage and wing cross-section. The larger engine placement must be visibly different and mechanically meaningful.

Evidence objects: A small angle-of-attack vane sensor cue on the nose, a subtle horizontal-stabilizer trim mechanism in the background, and blank folded-paper training/certification paperwork. The paperwork must have no readable text.

System clue: One dry cyan vellum signal trace from a single sensor toward a hidden stabilizer correction path. It must feel like dry vellum or a paper light trace, not water, liquid, a route overlay, or UI.

Composition: Sparse editorial composition, no crash spectacle, no wreckage, no fire, no explosion. Keep the right side lower-detail and safe for a fixed right rail occupying the right third of the 16:9 frame. Keep the public aircraft anchor readable on the left/center. No generated title text.

Style constraints: cascade-paper-architectures-ink-lit-v1, deep ink-blue field, warm cream paper forms, muted lavender shadows, dry cyan vellum glow, restrained coral warning accent, foam-core cut edges, translucent vellum, controlled model-light shadows, subtle paper fiber only, clean low-detail paper planes, no speckle/noise/grain/grit/sandy texture.

Hard exclusions: readable text, labels, logos, Boeing logo, airline logo, tail number, airline livery, MCAS screen text, AI robot, villain figure, pilots' faces, victims, executives, public officials, crash scene, wreckage, explosion, fire, ocean impact, falling aircraft, dense evidence board, arrows, UI overlays, diagnostic connector lines, gritty documentary noir, smoke, debris, high-frequency paper grain, sandy surface, water, waterfall, river, stream, canal, liquid spill, glowing watercourse, generated title lettering.

## Required Review Reads After Generation

- historical_accuracy_read
- source_reference_alignment_read
- public_anchor_geometry_read
- 737_max_aircraft_profile_read
- leap_engine_placement_read
- angle_of_attack_sensor_cue_read
- mcas_stabilizer_mechanism_read
- single_sensor_assumption_read
- training_commonality_document_cue_read
- generated_text_logo_read
- human_presence_read
- no_recognizable_faces_read
- no_crash_spectacle_read
- texture_noise_read
- waterfall_read

## Output Handling

After built-in ImageGen creates the candidate under `/Users/mike/.codex/generated_images/`, copy the selected image into:

`/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_a_20260519.png`

Then write a source-art candidate manifest with the built-in generated source path/hash, workspace copy path/hash, prompt path/hash, `generation_tool_provenance_read`, `imagegen_skill_read`, and all required review reads. The candidate must remain `review_ready`; it cannot be `keep` without human source-art review.
