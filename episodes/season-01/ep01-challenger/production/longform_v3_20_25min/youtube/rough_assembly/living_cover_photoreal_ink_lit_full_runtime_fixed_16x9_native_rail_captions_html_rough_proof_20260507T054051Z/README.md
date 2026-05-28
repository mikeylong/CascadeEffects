# Challenger Living Cover Native Rail Captions HTML Rough Proof

Review-only full-runtime HTML proof for the Challenger Living Cover.

## What Changed

- Records the prior fixed 16:9 larger-chapter-label rail proof as `tighten` because captions were missing from the rail.
- Adds browser-native WebVTT cue behavior to the lower-right side of the fixed right rail.
- Keeps the existing `<track kind="captions">` source referenced in place and mirrors active browser `TextTrack` cue text into the rail.
- Strips visible `SPEAKER_##:` diarization prefixes only for display.
- Uses rail-native typography and colors: no caption card, badge, border, glow, new accent, or Shorts-final visual styling.

## What Did Not Change

- Kept Variant C remains the back plate.
- Full approved audio, VTT captions, SRT transcript, and timing remain referenced in place.
- Fixed `1920x1080` canvas, `760px` rail, full-runtime 8-section timing, and staged 120/360/600ms transition behavior remain preserved.
- No MP4/MOV was rendered.
- No audio, captions, transcript, or video media were copied into this packet.
- No final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Review URL

`/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_fixed_16x9_native_rail_captions_html_rough_proof_20260507T054051Z/player.html`

## Review Question

Reply with exactly one disposition for this HTML rough proof: `keep`, `tighten`, or `reject`.

## Native Caption Review Note

Because Chromium blocks `file://` text-track loads, this packet should be reviewed through a local HTTP server from the packet root. The player uses local symlinks for the approved source art, audio, and VTT so the browser can load native cues without copying or modifying media.

## Local HTTP Review URL

`http://127.0.0.1:8787/player.html`

The server command is `python3 -m http.server 8787 --bind 127.0.0.1` from this packet root.

## Human Disposition Update - 2026-05-07T15:07:24Z

Recorded as `tighten`: the browser-native caption behavior is right, but the `32px` caption text is too small for YouTube long-form narration. This packet is not an advancement source; the next review artifact is the larger native rail captions HTML proof. Downstream render/final/Shorts/publish/YouTube flags remain `false`.
