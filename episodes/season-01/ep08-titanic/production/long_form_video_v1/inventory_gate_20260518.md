# Titanic Long-Form Inventory Gate

Episode: Titanic and the Lifeboat Regulation Gap
Workflow: `long_form_video_production_v1`
Date opened: 2026-05-18
Disposition: `keep_opened_for_package_audio_gate`

## Current State

- Long-form production root: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1`
- Source writer packet: `/Users/mike/Downloads/cascade-effects-writer-packets-01-08/episode-08-titanic-writer-packet.md`
- Source writer packet SHA-256: `aa065bfaf8884f89a00fd3fdb30ca2e2e5af4d9abde2f8ab3d729ae8e68a1e77`
- Long-form script candidate: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Long-form script candidate SHA-256: `38056564c66cb5249d02f37dffaf98c4acdea680465e1d9b93d01d06102e38cc`
- Long-form script word count: `1849`
- Long-form fact check: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/fact_check.md`
- Long-form fact check SHA-256: `9fc695539a22737d739f957e34a6a626cc685e349803613808449892effd335f`
- Long-form source pull sheet: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/source_pull_sheet.md`
- Long-form source pull sheet SHA-256: `d8e0e91fbadeb722280b1d873bf6d0a79b1daed78a99581e2f67e830bd56dbba`

## Existing Short Bridge

- Status: `private_review_upload_processed_manual_studio_checks_pending`
- Video ID: `ufYl87LFBXE`
- URL: `https://www.youtube.com/watch?v=ufYl87LFBXE`
- Role: bridge/discovery asset only
- Source-of-truth status: `false`

## Audio Inventory

- Long-form audio master status: `missing`
- Long-form audio pipeline: `not_started`
- Voice profile target: `longform_mike_v1`
- Short audio exists at `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1`, but it is Short-only and cannot satisfy any long-form audio gate.

## Gate Reads

- `source_writer_packet_read`: pass
- `longform_script_candidate_read`: pass
- `longform_fact_check_read`: pass
- `source_pull_sheet_read`: pass
- `existing_short_bridge_read`: pass_available_private_review_manual_phase
- `short_assets_long_form_source_of_truth`: false
- `frontier_model_script_critique_read`: pass
- `critique_integration_read`: pass_no_script_changes_required
- `human_script_approval_for_audio_read`: missing
- `longform_audio_master_read`: missing
- `audio_source_integrity_read`: missing
- `caption_timing_source_read`: missing

## Next Required Gate

Human script approval for audio render. No long-form audio render, visual-system planning, source-art generation, rough proof, final render, publish package, YouTube upload, or visibility action may start before the script/audio authorization gate passes.
