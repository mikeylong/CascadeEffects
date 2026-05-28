# Hyatt Regency Final MP4 Assembly Review

Packet: `hyatt_longform_final_mp4_20260519T011704Z`
Gate: `final_assembly_gate`
Status: `review_ready_pending_human_keep`
Human disposition: `pending`

## Output

- MP4: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_marked_region_ambient_reference_match_20260518T193011Z/video_render/hyatt_longform_final_mp4_20260519T011704Z/hyatt_regency_living_cover_final_review_1080p24.mp4`
- Duration: `869.034s`
- Render: `1920x1080`, `24fps`, H.264 video / AAC audio
- SHA256: `c3e7a3ca7ce13f4562828c7e95203fc7ffb185e642d56442675af124ca43346b`
- YouTube upload VTT sidecar: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_marked_region_ambient_reference_match_20260518T193011Z/video_render/hyatt_longform_final_mp4_20260519T011704Z/youtube_sidecars/hyatt_regency_longform.script_locked_rail_safe.offset_intro_9s601.vtt`

## What Changed

- Rendered the kept Hyatt HTML proof as a full-runtime MP4.
- Preserved the N6 source art, live-load pronunciation repair, right-rail-only text, staged chapter motion, camera flashes, and balloon rises while repairing the Challenger-style VO-to-outro blend and titleless three-target YouTube end screen.
- Burned script-locked rail captions into the video and copied the offset VTT/SRT sidecars for the final MP4 timeline.
- Kept publish readiness, private upload, YouTube action, and public release locked.

## QA Reads

| Read | Result |
|---|---:|
| MP4 created | `pass` |
| current kept source | `pass_rendered_from_current_kept_hyatt_html_proof` |
| H.264 video | `pass_h264_present` |
| AAC audio | `pass_aac_audio_present` |
| duration | `pass` |
| dimensions | `pass` |
| fps | `pass` |
| full decode | `pass` |
| caption script lock | `pass` |
| caption sidecar | `pass_upload_sidecar_uses_intro_offset_final_mp4_timeline` |
| burned rail captions | `pass_rendered_from_browser_rail_caption_layer` |
| right rail text | `pass` |
| out-of-rail text | `pass_no_visible_out_of_rail_text` |
| ordinal labels | `pass_no_visible_ordinal_chapter_labels` |
| end-screen text | `pass_no_end_screen_text` |
| chapter transition | `pass` |
| no speed regression | `pass_duration_and_fps_match` |
| downstream gates | `pass_final_assembly_review_ready_publish_upload_youtube_flags_false` |

## Human Review Options

Please reply with exactly one disposition for this final MP4 assembly: `keep`, `tighten`, or `reject`.
