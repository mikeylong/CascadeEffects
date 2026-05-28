# Source Art Exploration Review Packet: ImageGen Locked Lighting Pair

## Review Question

Review the A/B/C lighting pairs. Does any candidate behave like a separately rendered low-intensity lighting plate that overlays the kept lights-on plate closely enough for the Living Cover lighting ramp?

Reply with exactly one: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

## Review Surfaces

- Contact sheet: `assets/contact_sheets/lighting_pair_contact_sheet_desktop.png`
- Low-candidate sheet: `assets/contact_sheets/lighting_pair_low_candidates_desktop.png`
- Per-candidate checker overlays: `assets/qa/overlays/*_checker_overlay.png`
- Per-candidate edge overlays: `assets/qa/overlays/*_edge_registration_overlay.png`
- Per-candidate difference maps: `assets/qa/overlays/*_amplified_difference_map.png`

## Required Reads

- `separate_plate_render_read`
- `lighting_source_intensity_read`
- `composition_registration_read`
- `edge_alignment_read`
- `crew_count_read`
- `shuttle_pad_geometry_preservation_read`
- `right_rail_safe_space_read`
- `generated_text_logo_watermark_read`
- `no_global_dimming_read`
- `no_launch_effects_read`

No downstream action is authorized by this packet.

## Human Review Update

- Disposition: `tighten`
- Reviewer note: A and C look like a match; B does not; C lighting intensity is not intense enough.
- Successor should use A/C as positive registration references, B as a negative reference, and generate brighter candidates.
- Downstream gates remain locked.
