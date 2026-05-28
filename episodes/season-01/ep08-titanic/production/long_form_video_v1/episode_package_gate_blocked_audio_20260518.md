# Titanic Episode Package Gate

Episode: Titanic and the Lifeboat Regulation Gap
Workflow: `long_form_video_production_v1`
Date: 2026-05-18
Status: `blocked_missing_human_audio_approval_and_long_form_audio`

## Package Inputs

- Source writer packet: `/Users/mike/Downloads/cascade-effects-writer-packets-01-08/episode-08-titanic-writer-packet.md`
- Source writer packet SHA-256: `aa065bfaf8884f89a00fd3fdb30ca2e2e5af4d9abde2f8ab3d729ae8e68a1e77`
- Long-form script candidate: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Long-form script SHA-256: `38056564c66cb5249d02f37dffaf98c4acdea680465e1d9b93d01d06102e38cc`
- Long-form fact check: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/fact_check.md`
- Long-form fact check SHA-256: `9fc695539a22737d739f957e34a6a626cc685e349803613808449892effd335f`
- Long-form source pull sheet: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/source_pull_sheet.md`
- Long-form source pull sheet SHA-256: `d8e0e91fbadeb722280b1d873bf6d0a79b1daed78a99581e2f67e830bd56dbba`

## Mechanism And Spine

- Mechanism: compliance mistaken for safety after regulation lagged behind ship scale.
- Primary episode question: What does the record say that the legend leaves out?
- Promise: Titanic was legal under the relevant lifeboat rules, and that legality reveals the system failure.
- Chapter spine:
  1. Enough by law.
  2. The familiar iceberg story is incomplete.
  3. The law measured tonnage, not people.
  4. The top category stopped tracking the ship.
  5. Compliance became confused with sufficiency.
  6. Davits showed a larger emergency was physically thinkable.
  7. Evacuation failure was adjacent but not identical.
  8. SOLAS reframed the question after the disaster.
- CTA/next path: use the existing Titanic Short as the discovery bridge after manual Studio review.

## Gate Reads

- `longform_audio_current_and_usable_read`: missing
- `frontier_model_script_critique_read`: pass
- `critique_integration_read`: pass_no_script_changes_required
- `human_script_approval_for_audio_read`: missing
- `audio_source_integrity_read`: missing
- `mechanism_read`: pass
- `promise_read`: pass
- `chapter_spine_read`: pass
- `existing_short_bridge_read`: pass_available_private_review_manual_phase
- `short_assets_long_form_source_of_truth`: false
- `may_advance_to_visual_system`: false
- `may_start_source_art`: false
- `may_start_rough_assembly`: false
- `may_render_final_mp4`: false
- `may_youtube_action`: false
- `public_release_ready`: false

## Blocker

The package cannot advance because human script approval for audio is missing and no long-form audio exists. The next required gate is explicit human script approval for the exact script path/SHA, followed by long-form audio render, timing provenance, audio source integrity, and human audio keep.
