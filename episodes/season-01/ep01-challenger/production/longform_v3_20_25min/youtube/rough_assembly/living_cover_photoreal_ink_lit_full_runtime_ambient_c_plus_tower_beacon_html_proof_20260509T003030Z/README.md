# Challenger Living Cover Ambient C Plus Tower Beacon HTML Proof

Review-only full-runtime HTML proof repairing the beacon integration problem.

## Human Disposition

- Disposition: `tighten`
- Reason: aircraft did not read as continuing into the open sky left of the tower, and the live review audio did not produce audible playback for the reviewer.
- Repair direction: create a successor preserving this Ambient C plus beacon stack, then change only the aircraft route coverage and review-audio control reliability.

This packet is copied from the known-good registered Ambient C proof and preserves the approved lights-on backplate, fixed `1920x1080` canvas, precise foreground matte, early aircraft passes, localized dust, practical light micro-life, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Adds `tower_beacon_pulse_v1` over the existing red tower-top beacon.
- Keeps Ambient C intact: practical light micro-life, seven distant aircraft point-light passes, and sparse localized dust are preserved.
- Uses procedural canvas radial glows only; no edited/generated source raster, no sprite asset, no CSS source-plate filter, and no source image change.
- Pulse is slow and eased: soft rise, brief peak, slower fall, and low resting glow across an approximately `3.6s` cycle.
- Keeps the beacon local so it does not wash the shuttle, tower, rail, crew, or sky.

Mask QA remains in this packet:

- `qa/foreground_matte_black_white.png`: white means open sky where ambient effects may render; black means foreground occluder.
- `qa/open_sky_allowed_overlay.png`: cyan indicates open sky.
- `qa/foreground_occlusion_overlay.png`: red indicates blocked foreground.
- `qa/foreground_matte_edge_registration.png`: matte edge over the source plate.

Open:

- `http://127.0.0.1:8800/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.
