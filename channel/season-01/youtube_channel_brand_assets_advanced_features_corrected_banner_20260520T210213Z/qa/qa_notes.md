# QA Notes

Status: `review_required` for the combined advanced-features package.

Banner correction: pass. The banner now uses the kept `evidence_desk_balanced_precision` channel banner from `/Users/mike/Episodes_CascadeEffects/Channel_Trailer/youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z` instead of the incorrect generated placeholder from the prior May 20 package.

- `banner_source_read`: pass; kept package manifest read.
- `banner_human_keep_read`: pass; approval receipt copied.
- `banner_status`: keep.
- `banner_may_advance`: true for the banner asset only.
- `combined_package_status`: review_required.
- `combined_package_may_advance`: false.
- `youtube_studio_updated`: false.
- `dimensions_read`: pass.
- `file_size_read`: pass.
- `safe_area_read`: pass.
- `profile_icon_alignment_read`: carried forward from clean-edge profile repair.
- `watermark_read`: carried forward from clean-edge watermark derivative.

No YouTube Studio update was performed.

## JudgmentKit Review

JudgmentKit was rerun after replacing the incorrect banner. Browser QA passed for desktop and mobile. The tool still returned non-pass for state/static evidence ingestion even after explicit evidence was provided, so this is recorded as `deferred_non_pass_evidence_not_ingested_by_tool`. The combined package remains `review_required`, `may_advance: false`, and `youtube_studio_updated: false`.
