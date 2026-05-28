# Challenger Living Cover Precise Foreground Matte Ambient C Review

Status: `tighten`.

Review the corrected Ambient C proof.

## What To Review

- The matte should precisely separate open sky from foreground backplate occluders.
- The tower, shuttle, launch pad, crawlerway, crew, ground, lights, and foreground details should block aircraft/dust.
- The right rail should not appear as a matte boundary.
- Aircraft lights should feel distant and disappear behind foreground structures before reappearing in open sky.
- Sparse dust should remain subtle and localized, with no smoke, haze, sparks, or launch effects.
- Rail, captions, source plate, audio timing, and scrubber behavior should match the prior proof.

## Required Human Response

Choose exactly one:

- `keep`
- `tighten`
- `reject`

## Review Reads

- `foreground_matte_precision_read`
- `tower_shuttle_pad_occlusion_read`
- `crew_foreground_occlusion_read`
- `aircraft_background_depth_read`
- `open_sky_preservation_read`
- `right_rail_mask_exclusion_read`
- `backplate_preservation_read`
- `localized_dust_mote_read`
- `no_smoke_haze_fire_read`
- `deterministic_ambient_read`
- `rail_caption_occlusion_read`
- `youtube_legibility_read`

No downstream video render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Tighten Note

This proof is not an advancement source. Human review requested an airplane enter within roughly the first 20 seconds.

## Disposition Update

- Human disposition: `tighten`.
- Human feedback: aircraft still pass in front of the shuttle foreground. Root cause recorded as coordinate mismatch: the visible source plate was scaled/drifted while the foreground matte and ambient canvas were evaluated in raw 1920x1080 coordinates.
- Downstream render/final/Shorts/publish/YouTube gates remain locked.
