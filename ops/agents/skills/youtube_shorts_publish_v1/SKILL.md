---
name: "youtube_shorts_publish_v1"
description: "Validate, upload unlisted review drafts, status-check, receipt, and explicitly delete Cascade Effects YouTube Shorts publish packages after final export."
---

# YouTube Shorts Publish v1

Use this skill only after a Cascade Effects Short has a keeper `video final` and a local YouTube Shorts publish package manifest. The source of truth is the package manifest, not an episode manifest.

This skill owns the post-final unlisted review workflow:

`publish package -> validate -> unlisted review upload -> processing/status check -> Studio checks -> public release decision`

Public release is out of scope for agents. Visibility changes to public or scheduled release remain manual YouTube Studio actions after platform checks.

## Scope

This skill may:

- validate a package with `ce orchestrate publish-package-check <manifest_path>`
- upload the package as an unlisted YouTube review draft with `ce orchestrate publish-package-upload <manifest_path> --privacy unlisted`
- check processing, privacy, and channel status with `ce orchestrate publish-package-status <receipt_or_video_id>`
- write and interpret immutable upload/delete receipts beside the package
- delete a mistaken review upload only after exact video-id confirmation with `ce orchestrate publish-package-delete <receipt_or_video_id> --confirm-video-id <id>`
- guide manual YouTube Studio checks before public release

This skill must not:

- upload a public or scheduled video
- make an unlisted video public
- upload or mutate captions sidecars in v1
- edit the final-export package before routing back to final export
- store OAuth client secrets, refresh tokens, or access tokens in repo artifacts
- use deprecated episode-level commands: `publish-check`, `publish-prepare`, `publish`, or `publish-status`

## Required Inputs

- `manifest_path` for a local `target: youtube_shorts` publish package
- validated keeper final metadata: `source_final.disposition: keep`, `source_final.reel_class: keeper short`, and `source_final.may_publish: true`
- upload MP4, title, description, tags, SRT, cover frame, review, final manifest, and declared SHA-256 values
- title, description, hashtags, and tags drafted or QA'd through [/Users/mike/CascadeEffects/ops/agents/skills/youtube_metadata_copywriting_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_metadata_copywriting_v1/SKILL.md), with public tags limited to viewer-facing search intent and episode-central entities
- YouTube OAuth credentials outside the repo, loaded from environment variables first or `/Users/mike/.config/cascade-effects/youtube/`
- explicit user confirmation at action time before upload
- exact `confirm_video_id` before delete

Upload/status credentials require `youtube.upload` plus `youtube.readonly`. API delete requires a delete-capable scope such as `youtube.force-ssl` or `youtube`; if that scope is unavailable, route delete through YouTube Studio manually and write or preserve the local delete note.

## Workflow

1. Validate the package.

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce orchestrate publish-package-check /absolute/path/to/youtube_upload_manifest.json
```

Block on validation issues. Treat rights, Paper Architecture music, source footage, and Content ID notes as warnings that must be reviewed before public release.

2. Confirm unlisted upload.

Before running upload, get explicit user confirmation for the specific manifest path and `--privacy unlisted`.

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce orchestrate publish-package-upload /absolute/path/to/youtube_upload_manifest.json --privacy unlisted
```

The command writes a review upload receipt beside the package with video ID, URL, authenticated channel, privacy, processing status, thumbnail result, validation warnings, and post-upload blockers.

3. Check status.

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce orchestrate publish-package-status /absolute/path/to/youtube_review_upload_receipt.json
```

Confirm the upload belongs to the expected channel, remains unlisted, and reaches a stable processing state before Studio review.

4. Run manual Studio checks.

Before public release, a human must verify:

- copyright/Content ID and music claims, including Paper Architecture
- altered-content disclosure; answer `Yes` for realistic generated or source-derived event visuals
- captions; burned-in captions cannot be disabled on YouTube, so review or remove uploaded/automatic captions if they duplicate the burned-in layer
- Shorts cover frame; the API thumbnail attempt is nonfatal and custom Shorts covers may require Studio or mobile Studio handling
- audience, description, tags, category, visibility, and any restriction warnings

5. Delete only with exact confirmation.

If a review draft is wrong, ask for exact confirmation in the form `Delete <video_id>` or an equivalent explicit instruction that includes the same video ID.

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce orchestrate publish-package-delete /absolute/path/to/youtube_review_upload_receipt.json --confirm-video-id VIDEO_ID
```

The delete receipt must retain the deleted video ID, confirmation text, verification result, and note that local package paths are retained.

## Output Packet

Return a concise packet:

```yaml
stage: unlisted review upload | platform checks | delete cleanup
episode_id:
short_id:
manifest_path:
upload_receipt_path:
delete_receipt_path:
youtube_video_id:
youtube_video_url:
channel_id:
privacy_status:
processing_status:
thumbnail_status:
validation_warnings:
studio_checks_required:
public_release_boundary: manual_youtube_studio_only
disposition: keep | tighten | diagnostic only | reject
blockers:
next_action:
may_advance: false
```

Only the coordinator may treat a completed unlisted review upload as advancement toward public release. A review upload receipt is not a public-release approval.

## Edge Cases

- If package validation fails, do not upload; route back to final export or the coordinator with exact issues.
- If YouTube credentials authenticate to the wrong channel, stop and do not upload.
- If thumbnail upload fails, treat it as nonfatal and require manual cover verification in Studio.
- If delete fails because the OAuth token lacks delete scope, route to manual YouTube Studio deletion and keep the upload receipt.
- If auto captions duplicate burned-in captions, remove or disable the duplicate caption track manually where Studio allows it; burned-in captions are part of the video pixels.
- If the user asks for public release, provide the Studio checklist and keep the action manual.
