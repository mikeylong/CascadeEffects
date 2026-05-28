# Publish-Readiness Backfill Prompt

Use this prompt to apply the Therac/Challenger publish-readiness fix to another Cascade Effects long-form video. A lifecycle `review.html` should exist before final assembly `keep`; after final assembly receives human `keep`, the same stable review ID becomes the full publish-readiness package.

```text
Apply the long-form publish-readiness backfill to EPISODE_ID.

If final assembly is not kept yet, create or refresh an HTML-first lifecycle review packet under the episode's `production/.../youtube/publish_readiness/` directory with `lifecycle_stage: "in_progress"` and the current review artifact embedded. If final assembly is kept, start from the kept final assembly MP4 and its render manifest and refresh the full publish-readiness package.

Required behavior:
- preserve the stable remote review ID as the episode ID, reusing `https://cascadeeffects.tv/reviews/publish-readiness/EPISODE_ID` that was created at episode inception;
- keep lifecycle/status refresh separate from publish-readiness refresh: lifecycle refresh never records final assembly `keep`, never opens upload, and must show current gate, blockers, and upload locks;
- copy or stage package-local assets: final MP4, upload VTT/SRT, thumbnail candidate, key QA frames, metadata packet, and any VO/music transition samples;
- create `review.html` as the primary review artifact, with native MP4 controls, the upload VTT attached as a `<track>`, compact QA jump buttons only, thumbnail/QA frames/metadata/chapters/rights/lock state visible, and no upload/publish action enabled;
- serve the package through a byte-range-capable local HTTP server and record the canonical review URL as `http://127.0.0.1:<port>/review.html`; do not treat `file://` as satisfying review;
- run a local media-ref check, JSON parse, ffprobe stream/duration check, and HTTP `200` plus MP4 `206` range probe;
- update the publish-readiness manifest with `html_primary_review_read`, `html_media_refs_read`, `html_native_video_scrub_read`, `html_range_server_read`, `html_canonical_review_url_read`, `publish_readiness_package_local_asset_copy_read`, `html_upload_lock_read`, `youtube_metadata_copywriting_read`, `public_metadata_copy_read`, and `public_tag_relevance_read`;
- for music-bearing episodes, carry the kept `subtle_tail_outro_v1` contract evidence into the package: transition sample, `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, source-continuity reads, and regression read;
- do not pass publish readiness from whole-mix level deltas alone; the review sample and stem-level under-VO masking read must show the outro does not crowd the final words;
- if off-machine review is requested, create or reference an unlisted YouTube upload in the Cascade of Effects channel and use that as the remote video host for cascadeeffects.tv; do not upload final MP4/MOV/M4V files to Vercel/Blob;
- for remote review, run `/Users/mike/CascadeEffects/apps/web` `npm run reviews:validate -- --packet <packet> --mode publish-readiness --review-id EPISODE_ID` first, then `npm run reviews:publish -- --packet <packet> --mode publish-readiness --review-id EPISODE_ID --receipt <unlisted-youtube-upload-or-status-receipt>` only after the unlisted YouTube receipt/status exists;
- record `remote_review_url`, `youtube_unlisted_review_upload_read`, `youtube_unlisted_review_privacy_read`, `remote_review_manifest_read`, and `remote_review_large_video_upload_block_read` when the remote review manifest is published;
- keep `publish_ready`, `youtube_upload_ready`, `public_release_ready`, `may_youtube_action`, and `upload_performed` false.

Do not make the video public or scheduled. The next human gate is publish-readiness `keep`, `tighten`, or `reject`; an unlisted YouTube upload for remote review requires explicit approval and remains review-only.
```
