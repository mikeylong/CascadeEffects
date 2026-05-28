# Other-Seven Outro Level Successor Audit

- Status: PASS
- Review index: http://127.0.0.1:8766/other-seven-source-credit-gap-outro-level-review-20260526T031512Z.html
- Audit JSON: /Users/mike/Episodes_CascadeEffects/other-seven-source-credit-gap-outro-level-review-20260526T031512Z-audit.json
- Audit SHA-256: 4e91b2cdd77f369b78fa3f607ee5548ca722bd309a8eda9e9372874ef0f50182
- Threshold: successor legal/late outro mean must be >= -19.5 dB; no window peak above -1 dB.
- Old 20260526T000900Z review set: blocked because it preserved quiet mixes.

| Episode | Old legal mean | New legal mean | New late mean | Prelap delta | Peak | Player audio | Status |
|---|---:|---:|---:|---:|---:|---|---|
| Therac-25 | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/therac-25_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| Hyatt Regency | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/hyatt-regency_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| Semmelweis | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/semmelweis_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| Tacoma Narrows | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/tacoma-narrows_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| Piltdown Man | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/piltdown-man_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| 737 MAX | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/737-max_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |
| Titanic | -22.1 | -17.1 | -16.7 | 0 | -3 | audio_successor/titanic_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav | PASS |

## Reads

- All review and root players point to `audio_successor/*_outro_plus5db_after_vo.wav`.
- The selected review audio URL for each episode responds with HTTP 206 byte-range support.
- Source-credit timing, legal end-screen timing, labels, borderless styling, captions, and upload blocks are unchanged from the source-credit rollout.
- Runtime browser QA and package HTTP 206 range probes pass for all seven packages.
- No MP4 render or YouTube upload was performed.
