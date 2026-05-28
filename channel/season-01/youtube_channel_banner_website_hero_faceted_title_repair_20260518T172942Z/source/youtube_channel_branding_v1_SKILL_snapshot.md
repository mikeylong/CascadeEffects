---
name: "youtube_channel_branding_v1"
description: "Research, plan, generate, review, and package Cascade Effects YouTube channel branding assets such as channel banners, profile-image derivatives, video watermarks, and channel-level visual surfaces with official-platform requirements first."
---

# YouTube Channel Branding v1

Use this skill whenever Cascade Effects needs YouTube channel-level visual branding: channel banners, banner candidates, profile-picture derivatives, video watermarks, channel identity mockups, podcast playlist cover derivatives for YouTube, or a critique of any of those assets.

This skill owns the channel-branding asset workflow:

`official research -> skill/requirements update -> implementation package -> QA review -> human keep -> manual YouTube Studio update`

It does not upload, publish, change visibility, change channel branding in YouTube Studio, or mark a candidate `keep` without human review.

## Required References

- Official guidance snapshot: [references/official_youtube_channel_branding_guidance_2026-05-17.md](references/official_youtube_channel_branding_guidance_2026-05-17.md)
- Cascade Effects visual source of truth: [/Users/mike/Web_CascadeEffects/brand](/Users/mike/Web_CascadeEffects/brand)
- Channel/profile icon keep package: [/Users/mike/Episodes_CascadeEffects/Channel_Trailer/youtube_profile_icon_ink_lit_alpha_circle_20260513T184427Z](/Users/mike/Episodes_CascadeEffects/Channel_Trailer/youtube_profile_icon_ink_lit_alpha_circle_20260513T184427Z)
- Paper Architectures visual guidance: [/Users/mike/.codex/skills/cascade-paper-architectures/SKILL.md](/Users/mike/.codex/skills/cascade-paper-architectures/SKILL.md)

Refresh the official guidance before implementation when the snapshot is more than 90 days old, when YouTube UI/requirements appear to have changed, or when the user asks for current/latest requirements.

## Non-Negotiable Workflow

1. Do the research.
   - Use official YouTube/Google sources first.
   - Save or update the requirements snapshot before producing assets.
   - Record exact dimensions, safe areas, file-size limits, supported formats, crop behavior, and platform-specific constraints.

2. Create or update the skill.
   - If the work reveals new rules, update this skill or its reference snapshot before implementation.
   - Do not treat a one-off plan as enough when the work will recur.

3. Do the implementation.
   - Produce a timestamped local review package.
   - Keep candidates as `review_required` until Mike explicitly keeps one.
   - Do not mutate YouTube Studio or previous approved packages.

If these steps are out of order, stop, mark any premature candidate package as `rejected_research_mismatch`, and restart from research.

## Channel Banner Requirements

For standard YouTube channel banners:

- The viewer-facing design target is the channel-header strip, not the full upload canvas.
- For desktop-style header candidates, start by designing a wide strip around `2048 x 340 px` unless current research or a human-selected reference channel indicates a different displayed crop.
- Treat the official `2048 x 1152` minimum and `2560 x 1440` recommendation as upload-canvas constraints/wrappers, not the primary creative composition.
- Default recovery-package upload wrapper is `2048 x 1152 px`, `16:9`, unless Mike explicitly asks for the larger recommendation.
- `2560 x 1440 px`, `16:9`, is the recommended TV/full-canvas size and may be generated as an optional TV preview or explicit final wrapper.
- Minimum acceptable upload is `2048 x 1152 px`, `16:9`.
- At minimum size, safe area for text/logos is `1235 x 338 px`.
- At `2560 x 1440`, use a centered safe area of approximately `1544 x 423 px`.
- File size must be `6 MB` or smaller.
- The same banner appears across desktop, mobile, and TV but crops differently.
- Final upload assets must not include visible safe-zone boxes, borders, frames, or guide overlays.
- Do not include extra file embellishments such as decorative shadows, borders, or frames.

## Cascade Effects Banner Strategy

A channel banner is a responsive background identity surface, not a thumbnail, contact sheet, end screen, episode montage, or logo replacement.

Default direction:

- Build a wide, shallow ink-lit Paper Architecture identity strip first.
- Let the approved circular CE profile icon carry the mark.
- For channel banners, include the exact title `Cascade of Effects` unless Mike explicitly asks for a no-title variant.
- The title must feel native to Paper Architectures: faceted folded-paper letterforms, cream/lavender polygon planes, foam-core bevel/extrusion, subtle scored-paper highlights, and restrained dry cyan/coral signal accents where useful.
- Use exact deterministic local text only; do not rely on generated title lettering.
- Keep the full title entirely inside the centered safe area.
- Reflect the channel's content, not only the abstract brand system. Default channel banners should include recognizable content anchors from the first-eight doctrine: aerospace launch/decision systems, medical/software trust, structural revision/load paths, bridge dynamics, evidence artifacts, cockpit/automation, maritime regulation, and institutional evidence trails.
- Integrate those anchors into one continuous Paper Architecture world. Do not present them as a contact sheet, thumbnail row, framed cards, or isolated episode montage.
- Keep any single episode from dominating unless the user explicitly asks for a temporary campaign banner.
- Avoid Challenger-only dominance for default channel branding.
- For website-hero variants, use the current CascadeEffects.tv homepage hero as a visual-system reference, not as a final crop by default. Preserve the cleaner folded-paper identity read, safe-centered deterministic faceted title, bridge/shuttle/Titanic framing language, deep ink-blue field, cream/lavender paper forms, and dry cause/effect signal grammar while adapting the composition to the shallow YouTube strip.
- For website-hero variants, use `faceted_paper_title` rather than a plain font mask with simple bevel. The title should read like folded paper architecture, not ordinary bold typography with effects.
- Website-hero variants must translate the hero's folded cascade terrain into dry folded paper/foam-core terraces. Do not let it read as literal water, ice, glacier, waterfall, river, stream, canal, or liquid.

## Candidate Types

Use one or more of these candidate lanes:

- `minimal_identity_field`: quiet, premium channel background with restrained exact paper-style title unless explicitly scoped as no-title.
- `folded_cascade_world`: broad Paper Architecture landscape showing cause/effect structure without a single-episode read.
- `title_bearing_safe_area`: exact local `Cascade of Effects` title inside safe area, styled as Paper Architecture letterforms, with crop-safe art outside.
- `website_hero_clean_identity`: calmer YouTube-channel adaptation of the current CascadeEffects.tv homepage hero. Use text-free generated source art derived from the approved website-hero visual grammar, then render exact local `Cascade of Effects` lettering with `faceted_paper_title` centered inside the safe area. Keep it cleaner than a content-dense montage while preserving recognizable bridge, shuttle, Titanic, folded cascade/terrain, and restrained evidence/system cues.
- `campaign_banner`: time-bound episode or launch campaign; requires explicit human scope.

## Hard Rejections

Reject candidates that:

- treat the full `2560 x 1440` upload canvas as the viewer-facing design instead of designing the visible banner strip first
- are a contact sheet, grid of thumbnails, or row of framed cards
- depend on details outside the safe area to understand the brand
- put text, logo, or important faces/objects outside the safe area
- duplicate the profile icon at large scale without a reason
- use generated title text for a final asset
- use a plain font title treatment for website-hero variants when a faceted folded-paper title is required
- include safe-zone boxes, borders, frames, UI chrome, or guide overlays in the final asset
- exceed `6 MB`
- use bright/daylight legacy Paper Architectures unless explicitly scoped as reference
- read as literal water, ice, glacier, waterfall, river, stream, canal, or liquid
- feel like a Challenger-only banner when the requested surface is general channel identity
- are so abstract that they fail to signal Cascade Effects' systems-failure, evidence-trail, and mechanism-led documentary content

## Implementation Package

Every implementation package must include:

- `manifest.json`
- `README.md`
- `assets/` final candidate visible strips and any wrapped upload-canvas variants
- `previews/` desktop/mobile/TV crop previews and safe-area overlays
- `qa/` contact sheet and QA notes
- `source/` prompts, references, source notes, and official requirement snapshot copy

Every manifest must record:

- `status: review_required` unless human-kept
- `official_requirements_read`
- `skill_workflow_read`
- `display_strip_target_read`
- `dimensions_read`
- `upload_canvas_read`
- `file_size_read`
- `safe_area_read`
- `crop_resilience_read`
- `profile_icon_alignment_read`
- `website_hero_alignment_read` when using `website_hero_clean_identity`
- `final_embellishment_read`
- `generated_text_read`
- `waterfall_read`
- `texture_noise_read`
- `youtube_studio_updated: false`

## QA Views

Generate review derivatives that show how the same banner behaves as:

- primary visible strip, default target around `2048 x 340`
- full `2560 x 1440`
- desktop banner crop
- mobile/tablet narrow crop
- TV/full-canvas crop
- safe-area overlay preview

The overlay previews are review artifacts only. Never promote overlay files as upload candidates.

## Output Contract

Return or save:

- the official-source requirements summary
- the skill/requirements files updated
- the implementation package path
- embedded previews/contact sheet when images are produced
- explicit status: `review_required`, `tighten`, `reject`, or `keep`

Keep `may_advance: false` until Mike picks a candidate.

## Example

Request: "Make better YouTube banner candidates."

Correct response path:

1. Read official YouTube banner guidance.
2. Inspect/confirm the viewer-facing displayed header-strip target, commonly around `2048 x 340` for the channels Mike is referencing.
3. Update this skill or its official-guidance snapshot if needed.
4. Build a timestamped candidate package with visible strip candidates first, plus compliant upload-canvas wrappers only as needed; keep text/logo inside the safe area, generate crop previews, and make no YouTube updates.

Incorrect response path:

- Build a banner from old local package assumptions before official research.
- Present contact-sheet or framed-card compositions as final banner candidates.
- Treat exploratory generated-title mockups as approved channel assets.
