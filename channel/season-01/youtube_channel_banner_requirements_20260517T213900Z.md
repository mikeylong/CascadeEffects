# YouTube Channel Banner Requirements - Cascade Effects

Status: `requirements_research_ready`

This is the requirements baseline for the next Cascade Effects YouTube channel banner candidate pass. It supersedes local guesses in `youtube_channel_banner_candidates_brand_safe_20260517T212808Z`, which is now marked `rejected_research_mismatch`.

## Official YouTube Requirements

- Upload minimum: `2048 x 1152 px`, `16:9`.
- Recommended upload size, especially for TV: `2560 x 1440 px`.
- Safe area for text/logos at the minimum size: `1235 x 338 px`.
- Equivalent safe area at `2560 x 1440`: approximately `1544 x 423 px`, centered.
- File size: `6 MB` or smaller.
- The banner is one image reused across desktop, mobile, and TV, but it is cropped differently by device/view.
- The image must accommodate large screens while keeping essential text/logo content inside the safe area.
- Do not include additional file embellishments such as shadows, borders, or frames.

Sources:

- YouTube Help, "Manage your channel branding": https://support.google.com/youtube/answer/10456525?co=GENIE.Platform%3DDesktop&hl=en
- YouTube Help, "Channel banner & profile picture tips": https://support.google.com/youtube/answer/12950272?hl=en

## Corrected Cascade Effects Brief

The banner should behave like a background identity surface, not a thumbnail, title card, contact sheet, or episode montage. The circular CE logo/profile image already identifies the channel in the header; the banner should support it rather than repeat or compete with it.

Recommended candidate directions:

1. `minimal_identity_field`
   - Deep ink Paper Architectures field with a restrained folded-cascade structure.
   - No big title unless needed; if title appears, keep it small and centered inside the safe area.
   - Most recognizable content remains abstract/atmospheric outside the safe area so crops still look intentional.

2. `system_failure_world`
   - A wide source-safe Paper Architecture landscape showing cause-and-effect structures, evidence terraces, and dry signal paths.
   - No episode-specific hero dominance.
   - No bordered cards, thumbnail tiles, or repeated logo marks.

3. `title_optional_clean_banner`
   - Exact deterministic `Cascade of Effects` title only if the review needs title-bearing options.
   - Title stays entirely inside the centered safe area.
   - Artwork outside safe area remains crop-safe and non-essential.

## Hard Rejections For Next Pass

- No contact-sheet/card montage as the final banner.
- No visible safe-zone boxes, borders, frames, or decorative outlines in final assets.
- No generated title typography unless explicitly marked as exploratory only.
- No large logo/profile-icon duplication competing with the circular avatar.
- No episode-specific Challenger-first banner unless Mike explicitly wants a temporary launch campaign banner.
- No extra tagline, upload schedule, or public copy unless explicitly requested.
- No candidate over `6 MB`.

## QA Required Before Review

- `dimensions_read`: `2560x1440`.
- `file_size_read`: `<=6 MB`.
- `safe_area_read`: all required text/logos fit inside centered `1544x423`.
- `crop_resilience_read`: desktop, mobile, and TV crops still look intentional.
- `profile_icon_alignment_read`: complements the approved circular CE icon without duplicating it.
- `final_embellishment_read`: no borders/frames/safe overlays in final banner files.
- `generated_text_read`: pass or explicitly exploratory-only.
