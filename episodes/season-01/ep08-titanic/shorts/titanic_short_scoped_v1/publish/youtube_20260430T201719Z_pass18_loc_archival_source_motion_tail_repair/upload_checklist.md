# Titanic Short Upload Checklist

status: ready_for_private_review_validation
public_release_boundary: manual_youtube_studio_only

## Package

- Upload MP4: `titanic_lifeboat_gap_pass18_loc_archival_source_motion_tail_repair_youtube_short.mp4`
- Suggested Shorts cover frame: `suggested_shorts_cover_frame.png`
- Clean SRT sidecar: `titanic_lifeboat_gap_pass18_clean_captions.srt`
- Title: `titanic_lifeboat_gap_title.txt`
- Description: `titanic_lifeboat_gap_description.txt`
- Tags: `titanic_lifeboat_gap_tags.txt`
- Manifest: `youtube_upload_manifest.json`

## Private Review Upload

- Run `/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check /Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/publish/youtube_20260430T201719Z_pass18_loc_archival_source_motion_tail_repair/youtube_upload_manifest.json`.
- Upload only after explicit action-time confirmation for this manifest and `--privacy private`.
- Do not make the video public or scheduled from agent tooling.

## Studio Checks Before Public Release

- Confirm copyright and Content ID checks.
- Confirm Paper Architecture music claim state.
- Confirm altered-content disclosure; answer Yes for realistic generated or source-derived event visuals.
- Confirm burned-in captions and remove or disable duplicate uploaded/automatic captions if needed.
- Confirm the Shorts cover frame in Studio or mobile Studio.
- Confirm audience, category, title, description, tags, hashtags, and visibility.
