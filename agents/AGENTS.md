# Agents Guidance

Use [/Users/mike/Agents_CascadeEffects/references/skills/cascade_effects_series_bible_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/cascade_effects_series_bible_v1/SKILL.md) for episode strategy, first-eight slate decisions, mechanism-led packaging, future-topic greenlights, and long-form editorial-bible alignment.

Use [/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md) for active long-form audio-only script production from writer packets. It owns:

`writer packet -> Claude long-form draft -> Codex fact-check -> approved long-form audio script -> Short derivation handoff`

Use [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md) for active YouTube Shorts production requests in this repo. It is the coordinator/gatekeeper for:

`fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final`

When the workflow scope manifest imports motion-reference video, require a DP-owned `archival footage review` inside the `visual research packet` stage before the visual beatmap is locked.

Use [/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md) for Shorts cinematography planning, workflow scope approval, DP research briefs, explicit legacy imports, and episode constraint ledger approval before visual research or still generation.

Use [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md) only when the coordinator routes the `video final` stage for caption timing, YouTube Shorts-style text caption overlays, final export, final manifest, and final QA.

Use [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md) only after a keeper final/export package exists, for package validation, unlisted YouTube review upload, status checks, receipts, and explicitly confirmed review-upload deletion. Public release remains a manual YouTube Studio action.

Use [/Users/mike/Agents_CascadeEffects/references/skills/podcast_launch_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/podcast_launch_v1/SKILL.md) for Cascade of Effects podcast launch, RSS setup, directory submission, YouTube podcast connection, and ongoing companion podcast release planning. It owns:

`podcast strategy -> show package -> host/RSS setup -> launch audio -> directory submission -> YouTube podcast connection -> post-launch release workflow`

Use [/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/SKILL.md) for Cascade Effects long-form YouTube video production, watchable audio essays, living-cover visuals, long-form video packaging, full-episode upload prep, and long-form video review packets. It owns:

`inventory -> episode package -> visual system plan -> rough assembly proof -> final assembly -> publish readiness -> post-publish learning`

Use [/Users/mike/Agents_CascadeEffects/references/skills/youtube_metadata_copywriting_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_metadata_copywriting_v1/SKILL.md) for Cascade Effects YouTube titles, descriptions, chapters, hashtags, tags, publish-readiness metadata copy, and metadata QA. It owns public copy only; upload and visibility actions stay with the relevant publish workflow.

Use [/Users/mike/Agents_CascadeEffects/references/skills/youtube_channel_branding_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_channel_branding_v1/SKILL.md) for Cascade Effects YouTube channel-level visual branding assets, including channel banners, profile-image derivatives, video watermarks, channel identity mockups, and channel branding critiques. It owns:

`official research -> skill/requirements update -> implementation package -> QA review -> human keep -> manual YouTube Studio update`

Media handling:

- any time an image, video file, or audio file is shared by the user or surfaced by an agent, embed the media directly in the chat with the available chat media syntax; do not provide only a path or filename unless the embedded media is also present
- for local production artifacts, include the local file path as supporting context when useful for traceability

Routing rules:

- route edits, critiques, or codification of agent-readable workflow docs, `SKILL.md` files, skill packages, routing rules, or durable agent instructions through [/Users/mike/.codex/skills/skillskill/SKILL.md](/Users/mike/.codex/skills/skillskill/SKILL.md) as the primary skill
- apply [/Users/mike/.codex/skills/write-like-mike/SKILL.md](/Users/mike/.codex/skills/write-like-mike/SKILL.md) to those workflow-skill tasks only after `skillskill`, and only for tone/readability; `skillskill` owns routing signal, output contract, edge cases, packaging, and validation logic
- this repo is in a Challenger-first Shorts production restart; active new visual production starts with Challenger only until a later scoped manifest explicitly opens another episode
- all prior Challenger, Hyatt, Therac, 737, keeper-registry, casebook, packaging, style, model-experiment, and visual constraint artifacts are legacy by default and inactive unless an exact file is DP-imported into the current workflow scope
- start active production from a source writer packet, fact-checked long-form audio-only script, derived short-specific script, approved short-specific audio, a narration map, a DP-approved workflow scope manifest, a DP research brief, visual research evidence, a research-driven visual beatmap, shot_plan_v2, and a DP-approved active constraint ledger before still generation
- if archival motion is in scope, require an archival footage review with exact local media paths, original source URLs, `strict clean` hygiene, `hybrid` archival role, `selective` analog look, and a narrow `1-3 primary videos plus small backup set` source pool before the visual beatmap is locked
- route long-form audio script production from an episode `writer_packet.md` through [/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md) before deriving a Short
- route short audio generation or refresh into [/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md](/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md) when short audio is missing, stale, or being revised
- route scope, research brief, legacy import approval, constraint updates, shot design, sub-beat planning, and motion-coverage planning into [/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md)
- route image and motion judgment through the active style skill, currently [/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md](/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md)
- Paper Architecture visual style is allowed only for CascadeEffects.tv website visual assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images; YouTube Shorts and long-form video assets must not use Paper Architecture for source art, stills, keyframes, motion, proof frames, final frames, cover frames, chapter cards, effect maps, in-video end screens, or video thumbnails
- route final caption overlays and publishable Shorts export through [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md) only after an approved `motion video proof`
- route post-final package validation, unlisted review upload, status checks, and confirmed review-upload deletion through [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md); never make a YouTube Short public programmatically
- route podcast launch, RSS host setup, podcast directory submission, YouTube podcast playlist/RSS connection, and podcast episode release packets through [/Users/mike/Agents_CascadeEffects/references/skills/podcast_launch_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/podcast_launch_v1/SKILL.md); keep RSS as the podcast source of truth and require human review at each phase gate
- route long-form YouTube video production, watchable audio essays, living-cover visuals, long-form video packaging, full-episode upload prep, and long-form video review packets through [/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/SKILL.md); use [/Users/mike/Web_CascadeEffects/brand](/Users/mike/Web_CascadeEffects/brand) design-system and illustration contracts as the visual source of truth and require human review at each phase gate
- for long-form YouTube video source art, use Codex ImageGen as the default primary production source for episode backplates, but never in Paper Architecture style; archival stills, source video frames, and deterministic local compositions are reference evidence unless a human-approved source-art exception names the episode, exact source paths, reason, source/rights risk, and affected outputs
- for long-form Living Cover source art, block default foreground clipboards, binders, folders, paperwork stacks, or generic admin props unless a human-approved episode exception names the exact object and why it is visually necessary; prefer implied action, anticipation, subject/event presence, layered depth, and compositions with credible ambient/effects affordances
- do not render, promote, or mark long-form voice audio `keep` until the exact script revision has frontier-model critique, critique integration or explicit deferral, and human approval for audio; `script.status = "locked"` is not enough
- route YouTube metadata copywriting, title/description/tag critique, public metadata QA, and publish-readiness copy cleanup through [/Users/mike/Agents_CascadeEffects/references/skills/youtube_metadata_copywriting_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_metadata_copywriting_v1/SKILL.md); keep upload, publish, schedule, and visibility actions out of this copywriting skill
- route YouTube channel banner, profile-image derivative, video watermark, channel identity mockup, and channel branding critique work through [/Users/mike/Agents_CascadeEffects/references/skills/youtube_channel_branding_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_channel_branding_v1/SKILL.md); do official research first, update the skill/requirements snapshot second, and only then implement assets
- route standalone particle experiments, ParticleScene exploration, and particle workbench feature branches into [/Users/mike/Particle_Playground](/Users/mike/Particle_Playground) / `mikeylong/Particle_Playground`; keep this repo focused on production orchestration integration
- do not promote stills, motion, or shorts outside the `keep` gate vocabulary
- do not activate any visual constraint because it appears in old archives, old manifests, prior model experiments, old proof reviews, keeper registries, or casebooks; use only the active episode constraint ledger for the scoped short
- do not read from `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, old manifests, or old constraint/casebook files unless the workflow scope manifest lists the exact DP-approved import path
- caption/text/logo/UI/poster controls are legacy defaults and inactive until the active episode constraint ledger approves the current scoped rule; YouTube Shorts-style captions belong only in `video final`
- long-form audio script production remains audio-only; long-form YouTube video production is routed through the long-form video skill, while vertical Shorts motion/video production remains the YouTube Short path
