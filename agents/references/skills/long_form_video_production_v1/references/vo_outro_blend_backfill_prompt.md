# VO/Outro Blend Backfill Prompt

Apply the long-form VO/outro blend backfill to `EPISODE_ID`.

Find the active kept rough proof, final render, audio mix manifest, and publish-readiness package if present. Audit the final VO into outro transition against the current series contract: the approved full outro source must enter only under the last 1-2 seconds of VO at a low bed level, stay clearly below the final spoken phrase, reach target level only after the voice ends, continue without restarting, and carry the end-screen window.

Required evidence:

- packet-local `vo_outro_blend_plan`;
- exported transition review sample around the final VO line into the first outro seconds;
- passing `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, and `music_contract_regression_read`;
- `review.html` displays or links the transition sample in the publish-readiness package.
- whole-mix pre/post level deltas are supporting evidence only; they do not prove that the final words are uncrowded.

If the episode lacks this evidence, mark the current final or publish-readiness package `tighten_missing_vo_outro_blend_gate`, do not upload, and create a successor audio mix and final render using the approved visuals, captions, metadata, and locks unchanged.

Keep all upload, publish, schedule, visibility, and public-release flags false until the repaired package receives human `keep` and separate explicit upload authorization.
