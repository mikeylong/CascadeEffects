# Piltdown Man Shorts Stage Ledger

- `episode_id`: `piltdown-man`
- `short_id`: `piltdown_man_short_scoped_v1`
- `created_at`: `2026-05-18T17:45:06Z`
- `current_stage`: `publish package pass 07 validation ready`
- `last_completed_stage`: `video final pass 07 CRT visible scanline keep`
- `production_status`: `pass07_final_keep_publish_package_rebuild_in_progress_public_release_blocked`
- `may_advance`: `false`

## Rehydration Note

The episode TOML referenced historical production sidecars that were missing from disk at implementation time. This ledger records the surviving source of truth: pass 07 final MP4, no-audio final MP4, pass 07 review sheets, the kept audio package, the cleaned caption SRT, and the long-form fact-check. The missing pass 05/pass 07 JSON sidecars were not treated as existing approvals.

## Completed Gates

| gate | read | artifact |
|---|---|---|
| `audio` | `keep` | `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/audio_package.json` |
| `video final pass 07` | `keep` | `/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/piltdown_man_short_scoped_v1/motion_video_proof/pass_03_no_freeze_legibility_repair/final_exports/piltdown-man_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/piltdown-man__house_crt_visible_scanline_signal_interruption_captioned_final.mp4` |
| `final export review` | `keep` | `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1/production/final_export_review_pass_07_crt_visible_scanline.md` |
| `final export manifest` | `rehydrated_keep` | `/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/piltdown_man_short_scoped_v1/motion_video_proof/pass_03_no_freeze_legibility_repair/final_exports/piltdown-man_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/piltdown-man__house_crt_visible_scanline_signal_interruption_final_export.json` |
| `rights/fair-use review` | `manual_review_required` | `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1/production/publish_rights_fair_use_review_pass_07.md` |
| `keeper lesson capsule` | `written` | `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1/production/keeper_lesson_capsule.md` |

## Next Gate

Build and validate a fresh YouTube Shorts publish package. Private review upload requires explicit action-time confirmation for the exact manifest path and `--privacy private`. Public release remains manual YouTube Studio only.
