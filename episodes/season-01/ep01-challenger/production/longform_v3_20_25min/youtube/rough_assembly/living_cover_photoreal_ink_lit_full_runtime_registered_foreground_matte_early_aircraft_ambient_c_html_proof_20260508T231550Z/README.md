# Challenger Living Cover Registered Foreground Matte Early Aircraft Ambient C HTML Proof

Review-only full-runtime HTML proof repairing the foreground-depth bug in the early-aircraft Ambient C direction.

This packet preserves the approved lights-on backplate, fixed `1920x1080` canvas, precise foreground matte, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Fixes the coordinate mismatch that let aircraft appear in front of the shuttle/tower/pad.
- Locks the visible source plate to exact `1920x1080` stage coordinates: no source-plate scale, drift, crop, or transform.
- Keeps the matte and ambient canvas in the same coordinate system as the visible image.
- Preserves the early first aircraft pass within roughly the first 20 seconds.
- Keeps Ambient C behavior: practical light micro-life, distant aircraft point lights, and sparse localized dust.

Mask QA remains in this packet:

- `qa/foreground_matte_black_white.png`: white means open sky where ambient effects may render; black means foreground occluder.
- `qa/open_sky_allowed_overlay.png`: cyan indicates open sky.
- `qa/foreground_occlusion_overlay.png`: red indicates blocked foreground.
- `qa/foreground_matte_edge_registration.png`: matte edge over the source plate.

Open:

- `http://127.0.0.1:8798/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.

## Beacon Pulse Tighten

- Human disposition: `tighten` for beacon-life addition only.
- Reviewer requested the red tower beacon fade in and out at a natural pace without raster graphic artifacts.
- A successor HTML-only packet may be created; downstream render/final/Shorts/publish/YouTube gates remain locked.
