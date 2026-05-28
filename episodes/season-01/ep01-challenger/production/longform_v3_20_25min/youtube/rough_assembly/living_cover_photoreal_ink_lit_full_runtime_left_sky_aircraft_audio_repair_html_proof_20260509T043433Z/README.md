# Challenger Living Cover Left-Sky Aircraft And Audio Repair HTML Proof

Review-only full-runtime HTML proof repairing two issues from the `ambient_c_plus_tower_beacon` packet: aircraft route coverage left of the tower and live review-audio reliability.

This packet preserves the approved lights-on backplate, fixed `1920x1080` canvas, precise foreground matte, Ambient C dust/practical-light layer, procedural tower beacon pulse, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Replaces the aircraft route table with seven deliberate full-sky point-light passes.
- Adds multiple routes that visibly continue into open sky left of the tower after crossing the foreground matte.
- Keeps aircraft clipped behind the registered foreground matte; lights disappear behind tower/shuttle/pad/crew and reappear only in open sky.
- Hardens the review audio path: direct control interaction primes `muted=false`, `volume=1`, exposes audio debug/play APIs, and keeps the WAV served by the packet-local range-capable server.
- Keeps dust, beacon, rail, captions, source plate, approved audio/VTT symlinks, and all downstream gates unchanged.

Open:

- `http://127.0.0.1:8801/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.
