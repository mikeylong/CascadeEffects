# Challenger Living Cover Precise Foreground Matte Early Aircraft Ambient C HTML Proof

Review-only full-runtime HTML proof repairing aircraft timing in the precise foreground matte Ambient C direction.

This packet preserves the approved lights-on backplate, fixed `1920x1080` canvas, precise foreground matte, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Moves the first distant aircraft point-light pass into the first 20 seconds.
- Preserves the precise foreground matte so aircraft/dust remain behind the tower, shuttle, launch pad, crawlerway, crew, ground, and foreground details.
- Keeps the right rail out of the matte asset; rail/caption occlusion remains a render-layer concern.
- Keeps all ambient effects deterministic and review-only.

Mask QA:

- `qa/foreground_matte_black_white.png`: white means open sky where ambient effects may render; black means foreground occluder.
- `qa/open_sky_allowed_overlay.png`: cyan indicates open sky.
- `qa/foreground_occlusion_overlay.png`: red indicates blocked foreground.
- `qa/foreground_matte_edge_registration.png`: matte edge over the source plate.

Open:

- `http://127.0.0.1:8797/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.

## Disposition Update

- Human disposition: `tighten`.
- Human feedback: aircraft still pass in front of the shuttle foreground. Root cause recorded as coordinate mismatch: the visible source plate was scaled/drifted while the foreground matte and ambient canvas were evaluated in raw 1920x1080 coordinates.
- Downstream render/final/Shorts/publish/YouTube gates remain locked.
