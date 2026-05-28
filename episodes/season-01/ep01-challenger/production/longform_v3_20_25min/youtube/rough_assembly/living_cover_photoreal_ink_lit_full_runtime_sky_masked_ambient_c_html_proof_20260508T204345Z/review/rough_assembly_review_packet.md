# Challenger Living Cover Sky-Masked Ambient C Review

Review the repaired Ambient C proof.

Status: `tighten`. Human review: the mask is wrong; it needs to follow the actual visible sky/foreground boundary rather than using broad polygonal exclusion regions.

## What To Review

- Distant aircraft lights should feel behind the shuttle/pad, disappearing when their route crosses foreground objects.
- Aircraft passes should vary direction and vector enough to feel incidental over a `21:29` runtime.
- Dust motes should be slightly more discernible in motion, but still sparse and localized.
- No smoke, haze, launch exhaust, sparks, full-frame grain, or decorative particle field should appear.
- Rail, captions, source plate, audio timing, and scrubber behavior should match the prior single-backplate proof.

## Required Human Response

Choose exactly one:

- `keep`
- `tighten`
- `reject`

## Review Reads

- `sky_mask_read`
- `aircraft_background_depth_read`
- `aircraft_vector_variety_read`
- `sky_occlusion_read`
- `localized_dust_mote_read`
- `dust_motion_read`
- `no_smoke_haze_fire_read`
- `deterministic_ambient_read`
- `rail_caption_occlusion_read`
- `right_rail_safe_space_read`
- `youtube_legibility_read`

No downstream video render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.
