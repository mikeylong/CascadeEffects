---
name: "youtube_metadata_copywriting_v1"
description: "Draft, critique, and QA Cascade Effects YouTube titles, descriptions, chapters, hashtags, and tags using official YouTube guidance, episode evidence, and public-metadata gates."
---

# YouTube Metadata Copywriting v1

Use this skill whenever a Cascade Effects YouTube surface needs public metadata copy: titles, descriptions, chapter labels, hashtags, tags, Shorts related-video copy, playlist placement copy, publish-readiness metadata, or a critique of any of those fields.

This skill owns the copy layer only. It does not upload, publish, schedule, change visibility, choose final thumbnails, or approve rights/disclosure status.

## Required References

- Official guidance snapshot: [references/official_youtube_metadata_guidance_2026-05-15.md](references/official_youtube_metadata_guidance_2026-05-15.md)
- Series strategy and voice: [/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md)
- Packet template: [templates/youtube_metadata_copy_packet_template.md](templates/youtube_metadata_copy_packet_template.md)

Refresh the official guidance before changing this skill if the source snapshot is more than 90 days old, if YouTube metadata rules appear to have changed, or if the user asks for current best practices.

## Scope

This skill may produce or review:

- long-form video title, alternate titles, description, chapters, hashtags, and tags
- YouTube Shorts title, description, hashtags, tags, and related-video copy
- publish-readiness metadata sections for HTML review packages
- copy QA reads for existing metadata
- revision notes that separate public copy from production diagnostics

This skill must not:

- use internal production terms in public metadata, including `long-form episode`, `publish-readiness`, `proof`, `render`, `sidecar`, `package`, `review surface`, or `upload candidate`
- turn research notes, source names, scholar names, or internal labels into tags unless they are central to public positioning
- stuff tags into the description
- write clickbait that the video does not satisfy
- invent source claims, rights status, or platform approvals
- make YouTube actions; upload and visibility remain owned by the relevant publish workflow

## Core Principles

Metadata is a viewer promise. It should tell the right person why this video is worth opening and then help YouTube understand the match between the title, description, tags, video content, and viewer search.

Titles:

- Be accurate first. If the title overpromises, weak retention can hurt the video more than a clever phrase helps it.
- Front-load the most specific promise or object. Do not append `| Cascade Effects` to video titles; YouTube already shows the channel name across its templates and surfaces.
- Keep titles succinct. Platform limit is 100 characters, but the target is normally tighter: roughly 45-75 characters when the promise still reads clearly.
- Choose the mode deliberately: `searchable` for direct topic demand, `intriguing` for broader curiosity, or `hybrid` for most Cascade Effects releases.
- Avoid all-caps, emoji, generic episode labeling, and vague abstractions.

Descriptions:

- Make the first two or three lines do the public work. They should describe the video before a viewer expands the description.
- The first two description lines must include a concrete hook, at least one search-relevant public noun, and the viewer payoff. If the copy could fit several episodes by swapping nouns, it fails `description_concrete_viewer_hook_read`.
- Use one or two main viewer-search phrases naturally in the title and description.
- Keep each description unique to the video. Do not rely on default channel boilerplate as the opening.
- Put chapters after the main description for long-form videos. Start at `00:00`, use at least three chapters, keep timestamps ascending, and write labels as viewer-facing mini-hooks.
- Put links, references, credits, playlists, and channel boilerplate after the main description and chapters.
- If corrections are needed, use YouTube's `Correction:` or `Corrections:` format and do not hide them in prose.

Plausible but weak copy:

- Reject copy that is accurate, polished, and safe but too abstract to help a viewer decide to watch.
- Reject openings that lead with format, brand, or thesis language instead of the video's concrete evidence.
- Treat stock documentary verbs such as `traces`, `explores`, `examines`, and `unpacks` as a warning sign unless the sentence names a specific viewer payoff.
- Rewrite internal-analysis shorthand such as `operating history`, `evidence changed shape`, `decision standard`, `system pattern`, or similar phrases into public nouns a viewer recognizes.
- Require search-relevant concrete nouns: the event, organization, object, warning, failure mode, decision, place, or public artifact. For Challenger, examples include `Challenger`, `NASA`, `O-ring`, `solid rocket booster`, `cold weather`, `smoke`, and `launch pressure`.

Tags and hashtags:

- Treat tags as secondary. Title, thumbnail, and description matter more for discovery and viewer decision-making.
- Use tags sparingly for viewer search intent, exact episode entities, acronyms, and common misspellings.
- Remove research-source, scholar, author, or incidental person-name tags unless the name appears in public title/description positioning or has explicit human-approved discoverability value.
- Do not put excessive tags in the description.
- Use hashtags only when they genuinely connect the video to a public topic cluster. Default to zero to three high-confidence hashtags, never a tag cloud.

Cascade Effects voice:

- Lead with the concrete mechanism, not the show label.
- Prefer evidence-led language: what changed, what warning was missed, what decision standard shifted.
- Keep the prose calm and precise. Avoid disaster sensationalism, generic mystery framing, and implementation vocabulary.
- Video title pattern: `[specific promise]`. Keep the channel/show name out of long-form and Shorts titles unless the surface is channel-level.

## Workflow

1. Gather the copy inputs.
Use the locked script, transcript, summary, chapter map, thumbnail candidate/text, target audience, rights/disclosure notes, and publish surface. If any source is missing, state the gap and produce a draft with explicit blockers.

2. Identify the viewer promise.
Write one sentence that names the topic, the tension, and the payoff. This becomes the title/description anchor.

3. Draft title candidates.
Produce one recommended title plus three to six alternates. Include mode labels: `searchable`, `intriguing`, or `hybrid`. Reject any title that the video or thumbnail cannot satisfy.

4. Draft the description.
Write the first lines as public-facing copy, then chapters, then optional links/CTA/credits. Keep internal review notes out of the public description.

5. Draft tags and hashtags.
Start from the video topic, entities, acronyms, and search terms. Remove research-source names and internal labels. Include common misspellings only when they are plausible search mistakes.

6. Run QA reads.
Record pass/tighten/reject values:

- `title_thumbnail_promise_read`
- `youtube_metadata_copywriting_read`
- `front_loaded_title_read`
- `description_first_lines_read`
- `description_concrete_viewer_hook_read`
- `chapter_format_read`
- `public_metadata_copy_read`
- `public_tag_relevance_read`
- `tag_minimal_role_read`
- `hashtag_policy_read`
- `spam_deception_policy_read`
- `metadata_human_keep_read`

7. Return a copy packet.
Use the template unless the caller asks for only a quick title or tag critique. Keep `may_advance: false` until a human keeps the metadata.

## Output Packet

Use this shape for full metadata work:

```yaml
stage: youtube_metadata_copy
surface: long_form | short | podcast_playlist | channel | other
episode_id:
source_inputs:
viewer_promise:
recommended_title:
alternate_titles:
description:
chapters:
hashtags:
tags:
qa_reads:
blockers:
human_review_required: true
disposition: draft | review_ready | keep | tighten | reject
may_advance: false
```

For a critique, lead with findings ordered by severity, then provide a revised copy block.

## Edge Cases

- If the video covers a tragedy, accident, or death, avoid spectacle. The copy should frame the mechanism and evidence, not exploit harm.
- If a scholar, author, company, or person is important in the research but not part of the public promise, keep the name out of tags and put source credit in references instead.
- If a strong title needs the thumbnail to complete the thought, record the dependency in `title_thumbnail_promise_read`.
- If the title is accurate but too abstract, rewrite toward the concrete object, decision, warning, or consequence.
- If the description is accurate but could apply to several episodes after swapping nouns, reject it as plausible but weak and rewrite toward concrete evidence, search nouns, and viewer payoff.
- If YouTube Shorts metadata is being drafted, keep descriptions shorter and route public upload actions through the Shorts publish skill.
- If long-form publish-readiness is being drafted, the HTML review package must show the copy directly and keep diagnostics separate.

## Example

Input:

```text
Topic: Challenger
Mechanism: smoke warning became normalized evidence and launch standard reversed
Thumbnail text: The Accident Had Begun
Bad tag candidate: Diane Vaughan
```

Expected output:

```yaml
recommended_title: "The Challenger Warning That Stopped Working"
description_regression_examples:
  weak: "This Cascade Effects long-form episode traces how a seal problem became operating history..."
  mediocre: "The launch-night decision did not start on launch night. A seal problem became operating history..."
  stronger: "Before Challenger broke apart, cameras had already caught the warning: smoke from the right solid rocket booster. This video follows how O-ring damage, cold-weather concerns, and launch pressure moved through NASA's decision process until a known risk started to look acceptable."
tags:
  - Challenger disaster
  - Space Shuttle Challenger
  - NASA
  - O-ring
  - Rogers Commission
  - normalization of deviance
  - engineering failure
  - system failure
  - risk management
qa_reads:
  description_concrete_viewer_hook_read: pass_smoke_booster_o_ring_cold_weather_nasa_launch_pressure
  public_tag_relevance_read: pass_removed_research_source_person_tag
```
