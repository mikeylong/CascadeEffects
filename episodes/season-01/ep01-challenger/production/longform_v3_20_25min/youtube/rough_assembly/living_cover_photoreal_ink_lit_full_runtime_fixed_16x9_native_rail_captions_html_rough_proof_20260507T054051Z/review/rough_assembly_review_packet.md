# Native Rail Captions Review Packet

## Review Target

- Packet: `living_cover_photoreal_ink_lit_full_runtime_fixed_16x9_native_rail_captions_html_rough_proof_20260507T054051Z`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_fixed_16x9_native_rail_captions_html_rough_proof_20260507T054051Z/player.html`
- Source plate: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png`
- Caption source: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/transcript_source/challenger_longform_v3_20_25min_recording_review.diarized.vtt`

## Human Review Reads

| Read | Status |
| --- | --- |
| native caption behavior | `pending_human_review` |
| caption phrase/cue-level behavior | `pending_human_review` |
| no karaoke caption timing | `pending_human_review` |
| rail typography match | `pending_human_review` |
| caption bottom rail fit | `pending_human_review` |
| caption spacing | `pending_human_review` |
| caption no embellishment | `pending_human_review` |
| caption VTT reference | `pass_referenced_only` |
| fixed 16:9 canvas | `pending_human_review` |
| no responsive rail reflow | `pending_human_review` |
| no rail scale hack | `pending_human_review` |
| right rail safe space | `pending_human_review` |

## Review Notes

Review the captions as part of the YouTube video frame, not as interactive web UI. The visible caption should sit quietly at the bottom of the right rail, use the same visual language as the rail, and avoid word-by-word karaoke behavior or any added caption flair.

## Locked Scope

HTML-only review proof. No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

## Native Caption Review Note

Because Chromium blocks `file://` text-track loads, this packet should be reviewed through a local HTTP server from the packet root. The player uses local symlinks for the approved source art, audio, and VTT so the browser can load native cues without copying or modifying media.

## Local HTTP Review URL

`http://127.0.0.1:8787/player.html`

The server command is `python3 -m http.server 8787 --bind 127.0.0.1` from this packet root.

## Human Disposition Update - 2026-05-07T15:07:24Z

Disposition: `tighten`. Reviewer note: caption behavior is correct, but `32px` reads too small for YouTube narration captions. Required next artifact: HTML-only proof with larger native rail captions. No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.
