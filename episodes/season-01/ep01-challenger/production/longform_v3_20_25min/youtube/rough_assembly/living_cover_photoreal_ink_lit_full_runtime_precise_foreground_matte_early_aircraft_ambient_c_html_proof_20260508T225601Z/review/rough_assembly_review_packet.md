# Challenger Living Cover Precise Foreground Matte Early Aircraft Ambient C Review

Review the corrected Ambient C proof.

## What To Review

- A distant aircraft light should enter within roughly the first 20 seconds.
- The early aircraft pass should still feel distant and natural, not distracting.
- Aircraft lights should disappear behind foreground structures before reappearing in open sky.
- The precise foreground matte should continue to block the tower, shuttle, launch pad, crawlerway, crew, ground, lights, and foreground details.
- Sparse dust should remain subtle and localized, with no smoke, haze, sparks, or launch effects.
- Rail, captions, source plate, audio timing, and scrubber behavior should match the prior proof.

## Required Human Response

Choose exactly one:

- `keep`
- `tighten`
- `reject`

## Review Reads

- `aircraft_early_entry_timing_read`
- `aircraft_background_depth_read`
- `aircraft_vector_variety_read`
- `foreground_matte_precision_read`
- `tower_shuttle_pad_occlusion_read`
- `crew_foreground_occlusion_read`
- `open_sky_preservation_read`
- `right_rail_mask_exclusion_read`
- `backplate_preservation_read`
- `localized_dust_mote_read`
- `no_smoke_haze_fire_read`
- `deterministic_ambient_read`
- `rail_caption_occlusion_read`
- `youtube_legibility_read`

No downstream video render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Disposition Update

- Human disposition: `tighten`.
- Human feedback: aircraft still pass in front of the shuttle foreground. Root cause recorded as coordinate mismatch: the visible source plate was scaled/drifted while the foreground matte and ambient canvas were evaluated in raw 1920x1080 coordinates.
- Downstream render/final/Shorts/publish/YouTube gates remain locked.
