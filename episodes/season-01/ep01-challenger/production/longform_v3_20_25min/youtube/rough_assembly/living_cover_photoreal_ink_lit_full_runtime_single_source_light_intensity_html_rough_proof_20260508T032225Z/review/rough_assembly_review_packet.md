# Rough Assembly Review Packet: Single-Source Light Intensity

## Review Question

Does the render-time lighting-intensity ramp work for the Challenger Living Cover while preserving the frozen rail/caption system?

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

## Player

- `player.html`
- Local HTTP review is recommended because browser-native VTT loading is used.

## Key Behavior

- The proof uses exactly one source image layer.
- The approved lit source art is darkened at render time with CSS filters at the start.
- Brightness, contrast, and saturation interpolate with the story-shaped `light_intensity` ramp across the full `00:21:29.131` runtime.
- No generated lights-off plate, no second source-art PNG, and no opacity-driven image reveal is used.

## Required Reads

- `single_source_lighting_intensity_read`: pending human review
- `lighting_intensity_ramp_read`: pending human review
- `dark_start_read`: pending human review
- `story_shaped_light_intensity_ramp_read`: pending human review
- `one_source_image_layer_read`: pass/computed QA
- `css_filter_intensity_math_read`: pass/computed QA
- `no_opacity_reveal_read`: pass/static QA
- `caption_behavior_read`: pass/computed QA
- `downstream_gate_lock_read`: pass

No render, final assembly, Shorts, publish readiness, or YouTube action is authorized.

## Human Review Update

- Disposition: `reject`
- Reviewer note: use ImageGen to create two separately rendered plates; the CSS/filter proof is dimming, not separate lighting-source intensity renders.
- Downstream gates remain locked: no MP4 render, final assembly, Shorts, publish readiness, or YouTube action.
