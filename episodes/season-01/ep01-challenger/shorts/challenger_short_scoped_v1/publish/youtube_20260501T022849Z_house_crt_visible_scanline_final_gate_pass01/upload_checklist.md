# Challenger Short Upload Checklist

status: ready_for_private_review_validation
public_release_boundary: manual_youtube_studio_only

## Package

- Upload MP4: `challenger_house_crt_visible_scanline_youtube_short.mp4`
- Suggested Shorts cover frame: `suggested_shorts_cover_frame.png`
- Clean SRT sidecar: `challenger_warning_softening_captions.srt`
- Title: `challenger_warning_softening_title.txt`
- Description: `challenger_warning_softening_description.txt`
- Tags: `challenger_warning_softening_tags.txt`
- Manifest: `youtube_upload_manifest.json`

## Private Review Upload

- Run `ce orchestrate publish-package-check youtube_upload_manifest.json`.
- Upload only after explicit action-time confirmation for this manifest and `--privacy private`.
- Do not make the video public or scheduled from agent tooling.

## Studio Checks Before Public Release

- Confirm copyright and Content ID checks.
- Confirm Paper Architecture music claim state.
- Confirm altered-content disclosure; answer Yes for realistic generated or source-derived event visuals.
- Confirm burned-in captions and remove or disable duplicate uploaded/automatic captions if needed.
- Confirm the Shorts cover frame in Studio or mobile Studio.
- Confirm audience, category, title, description, tags, hashtags, and visibility.
