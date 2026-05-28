# Challenger Living Cover Registered Foreground Matte Early Aircraft Ambient C Review

Review the corrected Ambient C proof.

## What To Review

- Aircraft lights should stay behind foreground structures: shuttle, tower, pad, crawlerway, crew, ground, lights, and foreground details.
- The first aircraft pass should enter within roughly the first 20 seconds.
- Aircraft should disappear cleanly behind foreground silhouettes and reappear only in open sky.
- The source plate should not drift relative to the matte; the image is locked to the same `1920x1080` coordinates as the matte and ambient canvas.
- Sparse dust should remain subtle and localized, with no smoke, haze, sparks, or launch effects.
- Rail, captions, source plate, audio timing, and scrubber behavior should match the prior proof.

## Required Human Response

Choose exactly one:

- `keep`
- `tighten`
- `reject`

## Review Reads

- `source_plate_matte_registration_read`
- `foreground_matte_coordinate_space_read`
- `foreground_matte_precision_read`
- `tower_shuttle_pad_occlusion_read`
- `crew_foreground_occlusion_read`
- `aircraft_background_depth_read`
- `aircraft_early_entry_timing_read`
- `aircraft_vector_variety_read`
- `open_sky_preservation_read`
- `right_rail_mask_exclusion_read`
- `backplate_preservation_read`
- `localized_dust_mote_read`
- `no_smoke_haze_fire_read`
- `deterministic_ambient_read`
- `rail_caption_occlusion_read`
- `youtube_legibility_read`

No downstream video render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Beacon Pulse Tighten

- Human disposition: `tighten` for beacon-life addition only.
- Reviewer requested the red tower beacon fade in and out at a natural pace without raster graphic artifacts.
- A successor HTML-only packet may be created; downstream render/final/Shorts/publish/YouTube gates remain locked.
