# 737 MAX Source-Art ImageGen Prompt - Right-Rail Repair

Use case: `historical-scene`

Asset type: `Cascade Effects long-form Living Cover source-art backplate, 1920x1080`

Style lane: `cascade-ink-lit-photoreal-v1`

Workflow: `long_form_video_production_v1`

Candidate set target: `candidate_k_to_n_right_rail_repair`

Style reads:

- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`

## Shared Prompt

Create a text-free, unbranded, photoreal editorial Living Cover backplate for a Cascade Effects long-form video about the Boeing 737 MAX and MCAS.

Scene: a rainy airport terminal/ramp view before departure, seen through terminal glass or from an adjacent ramp/engineering vantage point. The image should feel historically anchored and public-scene credible, not like a generic evidence table or diagram.

Main subject: a recognizable unbranded 737 MAX-family aircraft, front-quarter nose and engine profile visible, with the larger forward/high-mounted engine relationship readable. Include subtle aviation mechanism cues only through real aircraft geometry: nose profile, angle-of-attack vane cue if naturally visible, engine placement, wing/tail/stabilizer relationship. Do not add diagnostic overlays, arrows, labels, UI paths, or visible MCAS graphics.

Human presence: include one or more anonymous human figures as distant or partially occluded aviation/maintenance/public-scene presence. No face-forward close-ups, no identifiable people, no celebrity/public-official/victim/pilot portrait.

Living Cover ambient affordance: the frame should give later motion something credible to animate: rain on glass, reflection shimmer, practical ramp lights, cockpit/window glow, wet tarmac reflections, distant service-vehicle movement, crowd attention, machinery readiness, or restrained environmental life.

Right-rail requirement: reserve the right third for `fixed_16x9_right_rail_v1` text, but make it scene-integrated. The right side must be low-detail and readable enough for rail typography while still visibly belonging to the same airport/ramp scene. Use dark rain glass, terminal mullions, soft reflection gradients, distant runway/ramp lights, weather surface, or atmospheric depth. Do not create a flat solid gray block, blank wall, opaque vertical slab, full-height rail panel, featureless dark rectangle, or placeholder area.

Composition: cinematic 16:9, 1920x1080, wide editorial frame. Aircraft and human/event attention should live left/center, with credible depth continuing into the right rail-safe region. Keep the right side low-contrast but not empty. Use layered foreground/midground/background depth.

Lighting: restrained rainy dusk or night airport lighting, practical ramp lights and glass reflections, natural photoreal color, no heavy stylization.

Avoid: website/channel brand-material style, craft-model aircraft treatment, miniature tabletop materials, logos, readable airline names, tail numbers, generated text, UI overlays, diagnostic connector lines, cyan traces, crash scenes, wreckage, fire, smoke spectacle, falling aircraft, gore, recognizable faces, foreground clipboards, binders, folders, paperwork stacks, legal pads, trays, generic evidence-table/admin props, courtroom/evidence-board layouts, gritty speckle, sandy texture, AI shimmer, waterfall/watercourse/cyan liquid path.

## Candidate Variation Directions

- `candidate_k_terminal_glass_depth`: terminal-glass view with right side as dark reflective rain glass and faint ramp-light depth, no solid block.
- `candidate_l_ramp_depth_lights`: ramp-side view with aircraft left/center and right side receding into low-detail wet tarmac, lights, and distant service motion.
- `candidate_m_gate_window_attention`: public terminal attention through rain-streaked windows, aircraft nose/engine centered left, right side carrying mullion/reflection depth.
- `candidate_n_engine_readiness_wide`: wider engine/readiness composition with anonymous maintenance figure and integrated right-side runway/ramp atmosphere.

## Required Output Checks

- 1920x1080
- text-free and logo-free
- no readable signage, livery, tail number, or UI text
- anonymous human presence only
- no foreground administrative props
- right side is rail-safe but source-visible and scene-integrated
- non-Paper long-form video source-art style
