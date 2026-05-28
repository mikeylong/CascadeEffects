# Cascade Effects Orchestration

`/Users/mike/Agents_CascadeEffects` is the orchestration layer for the Cascade Effects production stack.

It owns:

- channel-level config
- canonical per-episode manifests
- derived episode state snapshots
- the internal `ce-orchestrate` helper that powers `ce orchestrate ...`

It does not replace the existing Viz CLI. The user-facing surface remains:

```bash
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate doctor
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate bootstrap --episode hyatt-regency
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate board
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate report
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate set-scene-archetype hyatt-regency primary_scene_hero challenger_mission_control
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate render-scene therac-25 console_alarm_hero
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate promote-scene therac-25 console_alarm_hero --asset /absolute/path/to/approved.png
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate render-packaging therac-25 therac_thumbnail
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate promote-packaging therac-25 therac_thumbnail --asset /absolute/path/to/approved.png
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate render-motion challenger launch_commit_dolly
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate promote-motion challenger launch_commit_dolly --video /absolute/path/to/proof.mp4
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate assemble challenger
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check /absolute/path/to/youtube_upload_manifest.json
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload /absolute/path/to/youtube_upload_manifest.json --privacy unlisted
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-status /absolute/path/to/youtube_review_upload_receipt.json
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-delete /absolute/path/to/youtube_review_upload_receipt.json --confirm-video-id VIDEO_ID
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate sync --all
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate validate challenger
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate brief challenger motion_assets
```

## Default Skills

Use the series bible skill for episode strategy, first-eight slate decisions, mechanism-led packaging, future-topic greenlights, and long-form editorial-bible alignment:

- [/Users/mike/Agents_CascadeEffects/references/skills/cascade_effects_series_bible_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/cascade_effects_series_bible_v1/SKILL.md)

Use the active Shorts production skill for production work. It is the coordinator/gatekeeper for:

`fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final -> publish package -> unlisted review upload -> platform checks -> public release decision`

When the workflow scope manifest imports motion-reference video, keep that top-level flow unchanged but require a DP-owned `archival footage review` inside the `visual research packet` stage before the visual beatmap is locked.

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md)

That skill routes long-form audio-only script work to:

- [/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/episode_production_v1/SKILL.md)

That skill routes short audio work to:

- [/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md](/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md)

And it routes DP scope, research, and constraint approval to:

- [/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md)

And it routes image and motion judgment to the active style skill, currently:

- [/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md](/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md)

It routes the `video final` stage to the final-export skill for caption timing, YouTube Shorts-style text caption overlays, final MP4 export, final manifest, and final QA:

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md)

It routes post-final package validation, unlisted review upload, status checks, receipts, and confirmed review-upload deletes to the publish skill. Public release remains a manual YouTube Studio decision:

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md)

Final captions are post-production overlays only. Generated stills and motion must stay free of baked-in captions, readable text, UI overlays, logos, and poster graphics.

For restarted Shorts, the visual-research packet must also map each beat or shot to a recognizable source anchor or an explicit DP-approved non-literal exception. If a contact-sheet candidate loses that anchor and reads as a generic evidence-room prop, the lane routes back upstream instead of advancing.

If archival motion is in scope, the archival footage review must also carry exact local media paths, original source URLs, `strict clean` hygiene decisions, `hybrid` archival role, `selective` analog-look decisions, and a narrow source pool capped at `1-3` primary videos plus a small backup set.

Long-form audio podcast and long-form video are future skills, not active routing.

Standalone particle experiments, ParticleScene exploration, and particle workbench feature branches now live in `/Users/mike/Particle_Playground` and the private `mikeylong/Particle_Playground` repository. This repo keeps only production orchestration integration for particle workbench assets.

Use episode-specific pilot docs as working state, not as the active workflow definition.

For YouTube Shorts, the orchestration model assumes:

- the coordinator is the single source of truth for stage advancement
- contact sheets are human-visible selection gates
- video proofs are timing and sequence gates
- the final-export skill is the only owner of publishable captioned Shorts finals
- mixed-review proofs never become final exports
- no specialist skill may skip directly to `video final`

The orchestration model assumes:

- scripts are already written and locked
- `fact_check.md` is required beside the locked script before `visual_research` can clear
- `visual_research` is the first active lane
- `visual_research` defines a cold-open opening sequence with period-specific objects, a focal subject object, and a subject-specific motion beat
- `audio`, `scene_stills`, and `packaging_stills` can all progress once `visual_research` is done
- `audio` reaches `done` only when the final master WAV exists, the QA transcript exists, and a human reviewer approves the package
- scene and packaging canonical outputs live under `/Users/mike/Viz_CascadeEffects/references/episodes/<episode_id>/<item_id>`
- motion renders must come from stills explicitly approved for motion
- assembly is an agent-run ffmpeg pipeline gated by machine-assemblable act coverage
- assembly can optionally compose a Base + FX shot by overlaying alpha motion assets on top of a base source before the final voiceover mux

## Layout

- `config/channel.toml`: stack roots and lane defaults
- `config/asset_archetypes.toml`: reusable scene and packaging defaults for manifest intake
- `episodes/*.toml`: canonical episode manifests
- `state/*.json`: generated sync state
- `orchestration/cli.py`: thin command dispatcher for `ce orchestrate ...`
- `orchestration/io.py`: context loading, manifest IO, bootstrap helpers, and state writes
- `orchestration/domain.py`: lane planning, validation, reports, board summaries, and briefs
- `orchestration/motion.py`: motion render and promotion helpers
- `orchestration/adapters/`: read-only sibling-repo adapters for Episodes, Audio, Viz, and Web
- `bin/ce-orchestrate`: internal helper invoked by `ce orchestrate ...`

## Review App

The reviewer app now lives in `/Users/mike/Inbox_CascadeEffects`.

- Primary launch surface: `/Users/mike/Inbox_CascadeEffects/bin/ce-inbox review-server`
- Compatibility commands remain here under `ce orchestrate review-inbox`, `review-action`, and `review-server`
- Canonical review state still lives in this repo under `episodes/*.toml` and `state/reviews/*.jsonl`

## Workflow Glossary

- Workflow phase: the lane-level production state such as `todo`, `review`, or `done`
- Review decision: the human decision on a reviewable item such as `pending`, `approved`, or `rejected`
- Audio freshness: whether the current final audio is still aligned with the latest approved research and fact-checking (`current`, `provisional`, or `stale`)
- Audio package sync: whether the manifest-backed review asset matches the latest packaged WAV plus QA transcript recorded in `audio_package.json` (`current`, `out_of_sync`, or `unknown`)

## Intake Workflow

- `ce orchestrate bootstrap --episode <episode-id>` creates a canonical episode manifest from the folder layout under `/Users/mike/Episodes_CascadeEffects`.
- `ce orchestrate bootstrap --all` seeds every local episode folder that does not already have a manifest.
- `visual_research` packages must specify the opening tableau for the narrated time period, including supporting period objects, the focal subject object, and the motion behavior that brings that subject into focus.
- `ce orchestrate report` prints aggregate lane counts, unresolved scene archetypes, packaging demand, and motion-ready episodes so the board scales past a handful of episodes.
- `ce orchestrate set-scene-archetype <episode_id> <scene_item_id> <archetype_id>` resolves an unresolved scene slot and assigns its episode-owned still workspace.
- `ce orchestrate render-scene <episode_id> <scene_item_id>` runs the certified Viz still pipeline for a resolved scene item and records the latest proof.
- `ce orchestrate promote-scene <episode_id> <scene_item_id> --asset <approved.png>` copies an approved scene still into its canonical episode-owned output path.
- `ce orchestrate render-packaging <episode_id> <item_id>` runs the certified Viz still pipeline for a thumbnail or shorts cover without requiring scene resolution first.
- `ce orchestrate promote-packaging <episode_id> <item_id> --asset <approved.png>` copies an approved packaging still into its canonical episode-owned output path.
- `ce orchestrate render-motion <episode_id> <motion_item_id>` dispatches by motion item `authoring_mode`: legacy items still stage the selected still through `handoff-i2v`, while `particle_workbench` items invoke `bin/ce workbench export-shot` and record the returned proof clip plus export manifest on the motion item. When a workbench motion item is referenced as an assembly overlay, the export switches to `--alpha` and targets a ProRes 4444 `.mov`.
- `ce orchestrate promote-motion <episode_id> <motion_item_id> --video <proof-video>` promotes a reviewed proof clip into the motion item’s canonical `output_path` and marks it `done`.
- `ce orchestrate promote-audio <episode_id>` promotes the latest packaged audio sidecar from `audio.pipeline_dir/audio_package.json` into `audio.master_path` and `audio.transcript_path`, resetting approval if the promoted package differs from the current review asset.
- `ce orchestrate assemble <episode_id>` derives an act-spine cut from approved scene and motion assets, optionally applies `assembly.compositions` as Base + FX overlay composites, renders a canonical MP4 with `ffmpeg`, and records `assembly.master_video_path`.
- `ce orchestrate publish-package-check <manifest_path>` validates a local publish package manifest without checking episode assembly state or platform credentials.
- `ce orchestrate publish-package-upload <manifest_path> --privacy unlisted` uploads the validated package as an unlisted YouTube review draft and writes a receipt beside the package.
- `ce orchestrate publish-package-status <receipt_or_video_id>` checks YouTube processing/privacy status for the review upload.
- `ce orchestrate publish-package-delete <receipt_or_video_id> --confirm-video-id <id>` deletes a mistaken review upload only after exact video-id confirmation and writes a delete receipt.
- Legacy episode-level publish commands are deprecated because publishable Shorts finals are package-based.

Final audio now reaches `done` only when the final master WAV exists, the QA transcript exists, the packaged WAV and transcript have been promoted into the manifest-backed review asset, and a human reviewer approves the package.

The March 30, 2026 Challenger failure case is now explicitly guarded: a compile-only ElevenLabs manifest or hotspot test does not replace the canonical review package. Only a packaged WAV plus QA transcript recorded in `audio_package.json` can be promoted for review.

## Publish Package Publishing

The final-export workflow produces a local publish package with a JSON manifest, upload MP4, metadata files, captions, review notes, and provenance. Validate that package, then upload it as an unlisted YouTube review draft:

```bash
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check /absolute/path/to/youtube_upload_manifest.json
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload /absolute/path/to/youtube_upload_manifest.json --privacy unlisted
/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-status /absolute/path/to/youtube_review_upload_receipt.json
```

The validator currently supports `target: youtube_shorts`. It checks required manifest fields, declared asset paths and hashes, YouTube Shorts MP4 geometry/duration/streams, approved keeper-final status, and rights/claim warnings. The upload command always uses unlisted visibility, does not schedule or publish publicly, and does not require long-form episode assembly state.

OAuth credentials are loaded from environment variables first, then `/Users/mike/.config/cascade-effects/youtube/`. Secrets must not be stored in repo artifacts. Upload/status require `youtube.upload` plus `youtube.readonly`. Deleting through the API requires a broader delete-capable scope such as `youtube.force-ssl` or `youtube`; otherwise delete the review draft manually in YouTube Studio and retain the local package.

Public release remains manual in YouTube Studio after copyright/Content ID, Paper Architecture music, altered-content disclosure, captions, and cover checks. Burned-in captions cannot be disabled on YouTube; review or remove uploaded/automatic captions if they duplicate the burned-in layer.

Deprecated commands:

- `ce orchestrate publish-check <episode_id>`
- `ce orchestrate publish-prepare <episode_id>`
- `ce orchestrate publish <episode_id>`
- `ce orchestrate publish-status <episode_id>`

## Workflow Diagram

- Editable Mermaid source: [`episode-workflow-swimlane.mmd`](./episode-workflow-swimlane.mmd)
- Shareable rendered PDF: [`episode-workflow-swimlane.pdf`](./episode-workflow-swimlane.pdf)

The Mermaid source is the version to update when the workflow changes. The PDF is the checked-in export for quick sharing and review.

## Visual Research Files

Visual research working files live in the episode repos, not here:

- `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/visual_research`
- `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/visual_research`

Each episode repo also needs a sibling `fact_check.md` beside the locked script.

Those files are referenced from the episode manifests and episode adapters so orchestration can validate them.
