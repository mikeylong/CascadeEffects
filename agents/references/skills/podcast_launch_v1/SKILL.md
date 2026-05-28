---
name: "podcast_launch_v1"
description: "Plan, prepare, review, launch, and operate the Cascade of Effects companion podcast with RSS as the source of truth and human review gates before each publishing phase."
---

# Podcast Launch v1

Use this skill for Cascade of Effects podcast launch, RSS setup, directory submission, YouTube podcast connection, and ongoing companion podcast release planning.

This skill owns the gated podcast workflow:

`podcast strategy -> show package -> host/RSS setup -> launch audio -> directory submission -> YouTube podcast connection -> post-launch release workflow`

The RSS feed is the source of truth. YouTube and YouTube Music are distribution surfaces, not the podcast system.

## Default Strategy

- Show title: `Cascade of Effects`
- Default subtitle: `Second-order consequences, hidden systems, and the stories behind how things change.`
- Default show description: `Cascade of Effects explores how small decisions, overlooked incentives, and hidden systems ripple outward into technology, culture, design, business, and everyday life. Each episode follows the chain reaction behind an idea, asking not just what happened, but what happened next.`
- Default format: `companion commentary`
- Default positioning: a slower, richer companion to the YouTube channel with deeper context, second-order consequences, cut material, listener questions, interviews, or production notes.
- Default host recommendation: Buzzsprout when repo automation alignment matters; Spotify for Creators when free/fast launch is the priority; RSS.com when automatic directory submission is the priority; Captivate, Transistor, Podbean, or Libsyn when paid workflow control matters.
- Default YouTube path for audio-first companion episodes: RSS import with private or unlisted initial review.
- Default launch cadence: Week 1 trailer, Week 2 first two episodes, then companion podcast episodes within 24 to 72 hours of related YouTube video releases.

Do not treat the podcast as direct YouTube audio extraction unless a human explicitly selects `audio edition`.

## Scope

This skill may produce:

- podcast launch brief
- show metadata packet
- cover art requirements
- trailer and episode production checklist
- RSS host setup checklist
- directory submission packet
- YouTube podcast connection recommendation
- post-launch release packet

This skill must not:

- publish publicly without human approval
- make YouTube videos public
- submit paid, sponsored, or endorsed content without explicit disclosure review
- treat YouTube as the canonical podcast feed
- duplicate a normal YouTube episode as an RSS static-image upload without human approval
- overwrite repo podcast release state unless implementation is explicitly requested
- bypass a phase gate because an artifact exists locally

## Phase Gates

Every phase starts with `may_advance: false`. A phase may move from `review_ready` to `keep` only after human review. If approval is ambiguous, keep `may_advance: false` and name the blocker.

### 1. Format Gate

Decide the launch format:

- `companion commentary` - default; podcast extends the YouTube essay.
- `audio edition` - adapted audio version of each YouTube episode.
- `ripple notes` - 5 to 12 minute standalone field-note episodes.

Human approval required before metadata, asset, host, or episode work advances.

### 2. Show Package Gate

Prepare and review:

- title, subtitle, description, category, language, explicit status, copyright, contact email, website, and owner details
- default subtitle and show description from Default Strategy, unless a human selects alternate show copy
- cover art direction and source file plan
- 3000 x 3000 PNG/JPG master art with no transparency
- 1280 x 1280 YouTube derivative from the same master

Human approval required before host or RSS setup.

### 3. Host/RSS Gate

Prepare and review:

- host choice and rationale
- host option set: Spotify for Creators, RSS.com, Buzzsprout, Captivate, Transistor, Podbean, or Libsyn
- owner email visible in the RSS feed for platform verification
- RSS show metadata
- feed privacy/publication settings
- platform-neutral RSS URL

Human approval required before any feed publication, directory submission, or YouTube RSS connection.

### 4. Launch Audio Gate

Prepare and review:

- 1 to 2 minute trailer
- first two launch episodes
- title, description, transcript policy, show notes, source links, and related YouTube links
- listening review notes
- rights and disclosure review

RSS audio export target: stereo MP3 or AAC, 44.1/48 kHz, 128 to 256 kbps, roughly -16 LKFS/LUFS, true peak under -1 dB FS. Practical default: MP3, 44.1 kHz, stereo, 128 or 192 kbps.

Human approval required before uploading, scheduling, or publishing audio.

Launch cadence default:

- Week 1: publish the 1 to 2 minute trailer.
- Week 2: publish Episode 1 and Episode 2 together.
- Ongoing: publish each companion podcast episode within 24 to 72 hours of the related YouTube video.

### 5. Directory Submission Gate

Prepare and review directory submissions for:

- Apple Podcasts
- Spotify
- Amazon Music
- Pocket Casts
- Podcast Index
- iHeartRadio or other host-supported directories

Human approval required for feed URL, platform accounts, content rights, availability, transcripts, contact info, and release timing before submission.

### 6. YouTube Connection Gate

Choose one path:

- `rss_import` - default for audio-first companion episodes; creates static-image videos from the RSS feed.
- `podcast_playlist` - use only when existing full-length YouTube videos are the podcast episodes.
- `none` - defer YouTube podcast connection.

Before connection, check duplicate risk. Do not publish both a normal full video and an RSS-generated static-image version of the same episode on the same channel without explicit human approval.

Human approval required for connection path, default visibility, duplicate policy, paid-promotion disclosure, and copyright/monetization review.

### 7. Post-Launch Gate

For each episode, prepare a release packet with:

- audio path or host episode reference
- title, description, transcript/show notes, source links, and related YouTube link
- platform links after approval
- status, blockers, and next action
- rights, disclosure, and listening-review status

Human review required before public release, scheduled release, YouTube visibility changes, or platform submission changes.

## Episode Packaging Patterns

Use these title patterns unless a human supplies a stronger episode-specific title:

```text
001: The Hidden Chain Reaction Behind [Topic]
002: What [Event/Product/Decision] Changed Next
003: The Second-Order Effects of [Topic]
After the Cascade: [YouTube Episode Title]
Ripple Notes: [One Specific Idea]
```

Use this show notes structure for episode packets:

```text
In this episode of Cascade of Effects, we look at [topic] and trace the ripple effects most people miss.

Watch the related video:
[YouTube link]

In this episode:
00:00 Opening
02:15 The first-order effect
07:40 The hidden incentive
14:05 What changed downstream
21:30 The bigger pattern

Links and references:
[Source 1]
[Source 2]

Follow Cascade of Effects:
YouTube: [link]
Podcast: [Apple/Spotify link]
Newsletter or website: [optional]
```

## Output Packet

Return this packet for every run:

```yaml
stage:
phase_gate:
show_title: Cascade of Effects
format:
rss_source_of_truth: true
host:
rss_feed_url:
episode_or_asset:
review_artifacts:
platform_targets:
youtube_path: rss_import | podcast_playlist | none
rights_review_required:
human_review_required: true
may_advance: false
disposition: draft | review_ready | keep | tighten | blocked
blockers:
next_action:
```

Only a clear human approval may set `disposition: keep` for a phase. Even then, keep `may_advance: false` unless the current task explicitly asks to prepare the next phase.

## Operating Rules

- If asked to launch the podcast from scratch, start at the Format Gate.
- If asked to create show assets, confirm the Format Gate is `keep` first; otherwise return a Format Gate packet.
- If asked to submit to directories, confirm Host/RSS Gate and Launch Audio Gate are `keep` first.
- If asked to connect YouTube, check RSS status and duplicate risk before recommending a path.
- If asked to publish an episode, return a Post-Launch Gate packet and require human approval before public or scheduled release.
- If repo release metadata exists, treat it as working state, not approval.
- If the task concerns YouTube Shorts, route to the active Shorts production or publish skill instead.
- If the task concerns long-form audio-only script drafting from writer packets, route to the long-form script production skill first.

## Edge Cases

- If the podcast includes host-read ads, sponsorships, endorsements, or paid promotion, block for disclosure review before YouTube connection or public release.
- If an RSS-imported YouTube episode needs new audio after publishing, treat the replacement as a new review item because YouTube creates a new video on re-ingest.
- If a back catalog import is requested, recommend private or unlisted review first and note that subscriber notification behavior differs for back catalog uploads.
- If Apple, Spotify, or host metadata disagree, use the RSS feed as the canonical metadata and list the mismatch.
- If a platform account or owner email is unavailable, return `blocked` with the missing credential or contact field.
