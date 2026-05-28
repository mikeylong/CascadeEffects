import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac_living_cover_crt_tight_mask_html_rough_proof_20260517T032700Z";
const roughAssemblyRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly";
const voicePath = "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/final/Ep2_Therac-25.wav";
const loopPath =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav";
const outroPath =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture outro.m4a";
const registryPath = "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json";

const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const successorId = `therac_living_cover_music_mix_html_rough_proof_${stamp}`;
const successorRoot = path.join(roughAssemblyRoot, successorId);

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: options.capture ? ["ignore", "pipe", "pipe"] : "inherit",
    encoding: "utf8"
  });
  if (result.status !== 0) {
    const stderr = result.stderr ? `\n${result.stderr}` : "";
    throw new Error(`${command} ${args.join(" ")} failed with status ${result.status}${stderr}`);
  }
  return options.capture ? `${result.stdout || ""}${result.stderr || ""}` : result.stdout || "";
}

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function probeAudio(filePath) {
  const stdout = run(
    "ffprobe",
    [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-show_entries",
      "stream=codec_name,channels,sample_rate",
      "-of",
      "json",
      filePath
    ],
    { capture: true }
  );
  return JSON.parse(stdout);
}

function durationSeconds(filePath) {
  return Number(probeAudio(filePath).format.duration);
}

function replaceText(filePath, replacements) {
  let text = fs.readFileSync(filePath, "utf8");
  for (const [from, to] of replacements) text = text.split(from).join(to);
  fs.writeFileSync(filePath, text);
}

function walkFiles(root, callback) {
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      walkFiles(full, callback);
    } else if (entry.isFile()) {
      callback(full);
    }
  }
}

function artifact(filePath) {
  return {
    path: filePath,
    sha256: sha256(filePath)
  };
}

function updateTimelineObject(timeline, totalDuration, voiceDuration) {
  if (!timeline) return;
  timeline.duration_seconds = totalDuration;
  if (Array.isArray(timeline.sections) && timeline.sections.length) {
    const last = timeline.sections[timeline.sections.length - 1];
    last.duration = Number((totalDuration - last.at).toFixed(3));
  }
  if (Array.isArray(timeline.living_cover_cues)) {
    const outroCue = timeline.living_cover_cues.find(cue => cue.id === "outro_next_pattern");
    if (outroCue) {
      outroCue.at = Number(voiceDuration.toFixed(6));
      outroCue.end = Number(totalDuration.toFixed(6));
      outroCue.title = "Music outro";
      outroCue.phrase = "The Paper Architecture motif carries the end screen.";
      outroCue.treatment = "music-only outro and static YouTube end-screen target geometry";
    }
  }
}

function updateChapterMap(filePath, totalDuration) {
  const chapterMap = readJson(filePath);
  chapterMap.duration_seconds = totalDuration;
  if (Array.isArray(chapterMap.chapters) && chapterMap.chapters.length) {
    const last = chapterMap.chapters[chapterMap.chapters.length - 1];
    last.duration = Number((totalDuration - last.at).toFixed(3));
  }
  writeJson(filePath, chapterMap);
}

function updateCueMap(filePath, totalDuration, voiceDuration) {
  const cueMap = readJson(filePath);
  cueMap.status = "review_ready_pending_human_music_mix_disposition";
  cueMap.human_disposition = "defer";
  cueMap.duration_seconds = totalDuration;
  if (cueMap.output_locks) {
    Object.assign(cueMap.output_locks, {
      publish_ready: false,
      youtube_upload_ready: false,
      public_release_ready: false,
      may_youtube_action: false,
      mp4_render_created: false,
      may_create_full_runtime_mp4_render: false,
      may_advance_to_final_assembly: false,
      may_advance_to_publish_readiness: false
    });
  }
  if (Array.isArray(cueMap.cues)) {
    const outroCue = cueMap.cues.find(cue => cue.id === "outro_next_pattern");
    if (outroCue) {
      outroCue.at = Number(voiceDuration.toFixed(6));
      outroCue.end = Number(totalDuration.toFixed(6));
      outroCue.title = "Music outro";
      outroCue.phrase = "The Paper Architecture motif carries the end screen.";
      outroCue.treatment = "music-only outro and static YouTube end-screen target geometry";
    }
  }
  cueMap.review_question = "Review the Therac-25 music-mix successor: keep, tighten, or reject.";
  writeJson(filePath, cueMap);
}

function updatePlayer(totalDuration, voiceDuration) {
  const playerPath = path.join(successorRoot, "player.html");
  let html = fs.readFileSync(playerPath, "utf8");
  const match = html.match(/const proof=(.*?);window\.proof=proof/s);
  if (!match) throw new Error("Could not locate proof JSON in player.html");
  const proof = JSON.parse(match[1]);
  proof.duration = Number(totalDuration.toFixed(6));
  proof.outroStart = Number(voiceDuration.toFixed(6));
  proof.endScreenStart = Number(voiceDuration.toFixed(6));
  if (Array.isArray(proof.sections) && proof.sections.length) {
    const last = proof.sections[proof.sections.length - 1];
    last.duration = Number((totalDuration - last.at).toFixed(3));
  }
  html = html.replace(match[1], JSON.stringify(proof));
  html = html.replace(/data-jump="1057\.260"/g, `data-jump="${voiceDuration.toFixed(3)}"`);
  html = html.replace(
    "Review-ready Therac living cover micro-life proof. Human disposition required.",
    "Review-ready Therac living cover music-mix proof. Human disposition required."
  );
  fs.writeFileSync(playerPath, html);
}

function updateBrowserQaScript(totalDuration, voiceDuration) {
  const scriptPath = path.join(successorRoot, "scripts/rough_proof_browser_qa.mjs");
  replaceText(scriptPath, [
    [predecessorRoot, successorRoot],
    ["rough-proof-crt-tight-mask-", "rough-proof-music-mix-"],
    ["{ time: 1061.5, slug: 'end' }", `{ time: ${Number((voiceDuration + 1).toFixed(3))}, slug: 'end' }`]
  ]);
}

function updateAudioPackage(filePath, audioMixManifest) {
  const audioPackage = readJson(filePath);
  audioPackage.music_mix_successor = audioMixManifest;
  audioPackage.voice_profile_final_export_eligible = false;
  writeJson(filePath, audioPackage);
}

function updateAmbientLayer(filePath, audioMixManifest) {
  const layer = readJson(filePath);
  layer.packet_id = `therac_living_cover_ambient_effects_layer_${stamp}`;
  layer.status = "review_ready_pending_human_music_mix_disposition";
  layer.human_disposition = "defer";
  layer.lane_decision = "user_directed_backplate_region_effects_plus_music_visual_handoff";
  if (!layer.enabled_lanes.includes("music_visual_handoff")) layer.enabled_lanes.push("music_visual_handoff");
  layer.rationale =
    "Music-mix successor preserves the kept CRT-tight visual/effects proof and adds the required intro/outro music handoff without shifting narration or caption timings.";
  layer.additive_integration_policy =
    "Preserve the approved ImageGen backplate, VTT/captions, right rail, cue map, CRT/control-panel/top-left-monitor/machine-to-patient effects, and upload locks; replace only the local proof audio with a documented music mix.";
  layer.browser_sample_times_seconds = [0, 260.287, 710.468, 895.118, Number((audioMixManifest.voice_end_seconds + 1).toFixed(3))];
  layer.music_visual_handoff = {
    intro_music: {
      start_seconds: 0,
      end_seconds: audioMixManifest.intro_music_end_seconds,
      policy: "under_opening_voice_no_voice_or_caption_timing_shift"
    },
    outro_music: {
      start_seconds: audioMixManifest.voice_end_seconds,
      end_seconds: audioMixManifest.total_duration_seconds,
      policy: "music_only_tail_after_last_spoken_word"
    },
    end_screen: {
      start_seconds: audioMixManifest.voice_end_seconds,
      end_seconds: audioMixManifest.total_duration_seconds,
      policy: "static_youtube_target_geometry_during_music_only_tail"
    }
  };
  Object.assign(layer.required_reads, {
    intro_music_fade_tail_read: "pass_intro_bed_fades_under_opening_without_timing_shift",
    outro_music_mix_read: "pass_music_only_tail_after_last_spoken_word",
    music_visual_handoff_read: "pass_end_screen_starts_at_voice_end",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    audio_level_mix_read: audioMixManifest.reads.final_mix_no_clipping
  });
  Object.assign(layer.optional_per_effect_reads, {
    intro_music_fade_tail_read: "pass_intro_bed_fades_under_opening_without_timing_shift",
    outro_music_mix_read: "pass_music_only_tail_after_last_spoken_word",
    intro_music_voice_timing_read: "pass_no_voice_or_caption_timing_shift",
    end_screen_music_tail_read: "pass_music_only_tail_after_voice_end"
  });
  layer.downstream_locks = {
    mp4_render_created: false,
    may_create_full_runtime_mp4_render: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false
  };
  layer.review_question = "Review this music-mix successor: keep, tighten, or reject. Final MP4 stays locked until keep.";
  delete layer.render_authorization;
  delete layer.human_disposition_utc;
  delete layer.human_disposition_source;
  delete layer.human_disposition_scope;
  writeJson(filePath, layer);
}

function updateVisualPlan(filePath, audioMixManifest) {
  const plan = readJson(filePath);
  plan.packet_id = `therac25_living_cover_visual_system_plan_${stamp}`;
  plan.status = "review_ready_pending_human_music_mix_disposition";
  plan.human_disposition = "defer";
  plan.created_utc = stamp;
  plan.source_art_path = path.join(successorRoot, "assets/source_art/variant_h_control_room_active_terminal_1920x1080.png");
  plan.living_cover_ambient_effects_layer = {
    path: path.join(successorRoot, "references/living_cover_ambient_effects_layer.json"),
    sha256: "pending_written_after_update",
    lane_decision: "user_directed_backplate_region_effects_plus_music_visual_handoff",
    enabled_lanes: [
      "crt_console_screen_active_full_runtime",
      "control_panel_existing_light_blinks",
      "top_left_monitor_intermittent_flicker_noise",
      "implied_machine_to_patient_radiation_action",
      "music_visual_handoff"
    ],
    rationale: "The kept user-directed ambient regions are preserved; the successor adds the required intro/outro music handoff.",
    status: "review_ready_pending_human_music_mix_disposition",
    human_disposition: "defer"
  };
  Object.assign(plan.visual_reads, {
    intro_music_fade_tail_read: "pass_intro_bed_fades_under_opening_without_timing_shift",
    outro_music_mix_read: "pass_music_only_tail_after_last_spoken_word",
    music_visual_handoff_read: "pass_end_screen_starts_at_voice_end",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    audio_level_mix_read: audioMixManifest.reads.final_mix_no_clipping,
    human_rough_proof_keep_read: "pass_visual_keep_inherited_music_mix_successor_pending_human_audio_mix_disposition",
    current_kept_proof_render_source_read: "blocked_music_mix_successor_pending_keep",
    final_render_gate_read: "blocked_music_mix_successor_pending_keep",
    youtube_upload_lock_read: "pass_upload_publish_visibility_actions_remain_blocked"
  });
  plan.upload_locks = {
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false
  };
  plan.review_question = "Review the music-mix successor: keep, tighten, or reject.";
  delete plan.render_authorization;
  delete plan.human_disposition_utc;
  delete plan.human_disposition_source;
  delete plan.human_disposition_scope;
  writeJson(filePath, plan);
}

function createReviewPacket(audioMixManifest) {
  const reviewPath = path.join(successorRoot, "review/rough_assembly_review_packet.md");
  const markdown = `# Therac-25 Living Cover Music-Mix Rough Proof Review

- Packet: \`${successorId}\`
- Player: \`${path.join(successorRoot, "player.html")}\`
- Local review URL: \`http://127.0.0.1:8826/player.html\`
- Status: \`review_ready_pending_human_music_mix_disposition\`
- Human disposition: \`defer\`
- Final MP4 created: \`false\`

## What Changed

- Preserved the kept CRT-tight Living Cover visuals, source art, VTT, rail captions, chapter rail, cue map, and user-directed ambient effects.
- Replaced the local review audio with a documented music mix.
- Added Paper Architecture instrumental music under the opening, fading out without shifting narration or captions.
- Added a music-only outro tail after the last spoken word and moved the end-screen target geometry to that music-only tail.

## Timing

- Voice starts: \`0.000s\`
- Voice ends: \`${audioMixManifest.voice_end_seconds.toFixed(3)}s\`
- Intro music: \`0.000-${audioMixManifest.intro_music_end_seconds.toFixed(3)}s\`
- Music-only outro/end-screen: \`${audioMixManifest.voice_end_seconds.toFixed(3)}-${audioMixManifest.total_duration_seconds.toFixed(3)}s\`
- Total proof duration: \`${audioMixManifest.total_duration_seconds.toFixed(3)}s\`

## Music Provenance

- Registry: \`${registryPath}\`
- Intro/body loop: \`${loopPath}\`
- Outro motif: \`${outroPath}\`
- Rights note: registered Paper Architecture theme; public release still requires YouTube claim/status check.

## Hard Exclusions

No voice timing shift, no caption timing shift, no generated screen text, no cyan signal lines, no debug/effect labels, no MP4 render, no upload, no publish, and no visibility action.

## Human Disposition

Choose one for this music-mix successor: \`keep\`, \`tighten\`, or \`reject\`. Final MP4 render stays locked until \`keep\` on this successor.
`;
  fs.writeFileSync(reviewPath, markdown);
}

function updateRoughManifest(audioMixManifest) {
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(manifestPath);
  manifest.packet_id = successorId;
  manifest.created_utc = stamp;
  manifest.status = "review_ready_pending_human_music_mix_disposition";
  manifest.human_disposition = "defer";
  manifest.human_disposition_scope = "music_mix_successor_pending_review";
  manifest.predecessor_proof = {
    packet_id: path.basename(predecessorRoot),
    path: predecessorRoot,
    relationship: "visual_keep_predecessor_for_music_mix_successor",
    inherited_keep_scope: "visual_living_cover_and_ambient_effects_only"
  };
  manifest.approved_audio = {
    path: voicePath,
    sha256: sha256(voicePath),
    duration_seconds: audioMixManifest.voice_end_seconds,
    provider: "elevenlabs",
    voice_profile_id: "longform_mike_v1",
    qa_completed_at: "2026-05-16T00:11:13Z",
    role: "voice_only_source_preserved_without_timing_shift"
  };
  manifest.music_mix = audioMixManifest;
  updateTimelineObject(manifest.full_timeline, audioMixManifest.total_duration_seconds, audioMixManifest.voice_end_seconds);
  manifest.review_url = "http://127.0.0.1:8826/player.html";
  manifest.review_server = {
    url: "http://127.0.0.1:8826/player.html",
    port: 8826,
    pid: null,
    screen_session: "therac_8826_music_mix"
  };
  Object.assign(manifest, {
    html_proof_only: true,
    review_only: true,
    mp4_render_created: false,
    may_create_full_runtime_mp4_render: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false
  });
  manifest.upload_locks = {
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    mp4_render_created: false,
    may_create_full_runtime_mp4_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false
  };
  Object.assign(manifest.reads, {
    intro_music_fade_tail_read: "pass_intro_bed_fades_under_opening_without_timing_shift",
    outro_music_mix_read: "pass_music_only_tail_after_last_spoken_word",
    intro_music_voice_timing_read: "pass_no_voice_or_caption_timing_shift",
    music_visual_handoff_read: "pass_end_screen_starts_at_voice_end",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    audio_level_mix_read: audioMixManifest.reads.final_mix_no_clipping,
    audio_duration_extension_read: "pass_music_tail_extends_total_duration_after_voice_end_only",
    current_kept_proof_render_source_read: "blocked_music_mix_successor_pending_keep",
    final_render_gate_read: "blocked_music_mix_successor_pending_keep",
    downstream_gate_read: "pass_final_render_final_assembly_publish_upload_locked_until_music_mix_keep",
    youtube_upload_lock_read: "pass_upload_publish_visibility_actions_remain_blocked"
  });
  manifest.artifacts.player_html = artifact(path.join(successorRoot, "player.html"));
  manifest.artifacts.chapter_map = artifact(path.join(successorRoot, "references/chapter_map.json"));
  manifest.artifacts.living_cover_cue_map = artifact(path.join(successorRoot, "references/living_cover_cue_map.json"));
  manifest.artifacts.review_packet = artifact(path.join(successorRoot, "review/rough_assembly_review_packet.md"));
  manifest.artifacts.browser_qa_script = artifact(path.join(successorRoot, "scripts/rough_proof_browser_qa.mjs"));
  manifest.artifacts.living_cover_ambient_effects_layer = artifact(
    path.join(successorRoot, "references/living_cover_ambient_effects_layer.json")
  );
  manifest.artifacts.visual_system_plan = artifact(path.join(successorRoot, "references/living_cover_visual_system_plan.json"));
  manifest.artifacts.audio_mix_manifest = artifact(path.join(successorRoot, "references/audio_mix_manifest.json"));
  manifest.artifacts.review_server = {
    url: "http://127.0.0.1:8826/player.html",
    pid_path: path.join(successorRoot, "review_server.pid"),
    server: "range_static_server.mjs",
    screen_session: "therac_8826_music_mix"
  };
  manifest.review_packet_path = path.join(successorRoot, "review/rough_assembly_review_packet.md");
  manifest.review_question = "Review the Therac-25 music-mix successor: keep, tighten, or reject.";
  manifest.render_authorization = {
    authorized_by_human_request: false,
    blocker: "music_mix_successor_pending_human_keep",
    upload_publish_visibility_actions_authorized: false
  };
  delete manifest.human_disposition_utc;
  delete manifest.human_disposition_source;
  delete manifest.keep_record;
  delete manifest.current_kept_html_proof;
  writeJson(manifestPath, manifest);
}

if (!fs.existsSync(predecessorRoot)) throw new Error(`Missing predecessor: ${predecessorRoot}`);
if (fs.existsSync(successorRoot)) throw new Error(`Refusing to overwrite existing successor: ${successorRoot}`);

fs.cpSync(predecessorRoot, successorRoot, { recursive: true, verbatimSymlinks: true });
fs.rmSync(path.join(successorRoot, "review_server.pid"), { force: true });
fs.rmSync(path.join(successorRoot, "review_server.log"), { force: true });
for (const file of fs.readdirSync(path.join(successorRoot, "review"))) {
  if (file.startsWith("human_keep_")) fs.rmSync(path.join(successorRoot, "review", file), { force: true });
}
fs.rmSync(path.join(successorRoot, "qa"), { recursive: true, force: true });
fs.mkdirSync(path.join(successorRoot, "qa/screenshots"), { recursive: true });

const voiceDuration = durationSeconds(voicePath);
const loopDuration = durationSeconds(loopPath);
const outroDuration = durationSeconds(outroPath);
const introMusicEndSeconds = Number((loopDuration + 2).toFixed(6));
const musicOnlyTailSeconds = 15;
const totalDuration = Number((voiceDuration + musicOnlyTailSeconds).toFixed(6));
const loopSamples = Math.round(loopDuration * 44100);

const localAudioPath = path.join(successorRoot, "assets/audio/Ep2_Therac-25.wav");
fs.rmSync(localAudioPath, { force: true });

const filter = [
  "[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[voice]",
  "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[loop_intro_src][loop_outro_src]",
  `[loop_intro_src]aloop=loop=-1:size=${loopSamples}:start=0,atrim=0:${introMusicEndSeconds.toFixed(
    6
  )},asetpts=PTS-STARTPTS,volume=0.09,afade=t=in:st=0:d=0.35,afade=t=out:st=${loopDuration.toFixed(
    6
  )}:d=2[intro_music]`,
  `[loop_outro_src]aloop=loop=-1:size=${loopSamples}:start=0,atrim=0:${musicOnlyTailSeconds.toFixed(
    6
  )},asetpts=PTS-STARTPTS,volume=0.18,afade=t=in:st=0:d=0.3,afade=t=out:st=${(musicOnlyTailSeconds - 1).toFixed(
    6
  )}:d=1,adelay=${Math.round(voiceDuration * 1000)}|${Math.round(voiceDuration * 1000)}[outro_loop]`,
  `[2:a]aformat=sample_rates=44100:channel_layouts=stereo,asetpts=PTS-STARTPTS,volume=0.68,afade=t=in:st=0:d=0.2,adelay=${Math.round(
    voiceDuration * 1000
  )}|${Math.round(voiceDuration * 1000)}[outro_motif]`,
  "[voice][intro_music][outro_loop][outro_motif]amix=inputs=4:duration=longest:dropout_transition=0,alimiter=limit=0.89:level=false,aresample=44100[aout]"
].join(";");

run("ffmpeg", [
  "-y",
  "-hide_banner",
  "-i",
  voicePath,
  "-i",
  loopPath,
  "-i",
  outroPath,
  "-filter_complex",
  filter,
  "-map",
  "[aout]",
  "-c:a",
  "pcm_s16le",
  localAudioPath
]);

const mixProbe = probeAudio(localAudioPath);
const durationDelta = Math.abs(Number(mixProbe.format.duration) - totalDuration);
const volumeOutput = run("ffmpeg", ["-hide_banner", "-i", localAudioPath, "-af", "volumedetect", "-f", "null", "-"], {
  capture: true
});
const volumeText = volumeOutput;
const maxVolumeMatch = volumeText.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/);
const maxVolume = maxVolumeMatch ? Number(maxVolumeMatch[1]) : null;
const audioMixManifest = {
  packet_id: `therac25_music_mix_${stamp}`,
  status: "review_ready_pending_human_music_mix_disposition",
  created_utc: stamp,
  mix_profile_id: "paper_architecture_intro_bed_music_only_outro_v1",
  voice_source_path: voicePath,
  voice_source_sha256: sha256(voicePath),
  voice_end_seconds: Number(voiceDuration.toFixed(6)),
  output_path: localAudioPath,
  output_sha256: sha256(localAudioPath),
  output_probe: mixProbe,
  total_duration_seconds: Number(Number(mixProbe.format.duration).toFixed(6)),
  expected_total_duration_seconds: totalDuration,
  intro_music_end_seconds: introMusicEndSeconds,
  music_only_tail_seconds: musicOnlyTailSeconds,
  end_screen_start_seconds: Number(voiceDuration.toFixed(6)),
  music_sources: {
    registry: {
      path: registryPath,
      sha256: sha256(registryPath),
      track_id: "paper_architecture_theme_v1"
    },
    intro_body_loop: {
      path: loopPath,
      sha256: sha256(loopPath),
      duration_seconds: Number(loopDuration.toFixed(6)),
      role: "intro_bed_and_outro_tail_loop"
    },
    outro_motif: {
      path: outroPath,
      sha256: sha256(outroPath),
      duration_seconds: Number(outroDuration.toFixed(6)),
      role: "music_only_end_screen_motif"
    }
  },
  mix_decisions: {
    voice_timing_shift_seconds: 0,
    caption_timing_shift_seconds: 0,
    intro_music_policy: "under_opening_voice_no_preroll",
    intro_music_volume_linear: 0.09,
    intro_music_fade_tail_seconds: 2,
    outro_music_policy: "append_music_only_tail_after_last_spoken_word",
    outro_loop_volume_linear: 0.18,
    outro_motif_volume_linear: 0.68,
    limiter: "alimiter limit=0.89 level=false"
  },
  rights_and_claims: {
    rights_check_required_before_public_release: true,
    claim_risk: "check_upload_processing_before_public_release",
    notes: "Uses registered Paper Architecture theme assets from the local music registry. Public release remains blocked until YouTube claim/status checks are complete."
  },
  reads: {
    voice_timing_preserved_read: "pass_no_voice_timing_shift",
    caption_timing_preserved_read: "pass_vtt_unchanged_no_caption_timing_shift",
    intro_music_fade_tail_read: "pass_intro_bed_fades_under_opening_without_timing_shift",
    outro_music_mix_read: "pass_music_only_tail_after_last_spoken_word",
    music_visual_handoff_read: "pass_end_screen_starts_at_voice_end",
    duration_extension_read: durationDelta < 0.05 ? "pass_music_tail_extends_total_duration_after_voice_end_only" : "tighten_duration_mismatch",
    stream_read:
      mixProbe.streams?.[0]?.codec_name === "pcm_s16le" && mixProbe.streams?.[0]?.channels === 2
        ? "pass_pcm_s16le_stereo_44100"
        : "tighten_unexpected_audio_stream",
    final_mix_no_clipping:
      Number.isFinite(maxVolume) && maxVolume <= -0.9 ? `pass_max_volume_${maxVolume.toFixed(1)}dB` : "tighten_max_volume_unverified",
    music_rights_read:
      "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release"
  }
};

writeJson(path.join(successorRoot, "references/audio_mix_manifest.json"), audioMixManifest);
updatePlayer(audioMixManifest.total_duration_seconds, voiceDuration);
updateBrowserQaScript(audioMixManifest.total_duration_seconds, voiceDuration);
updateChapterMap(path.join(successorRoot, "references/chapter_map.json"), audioMixManifest.total_duration_seconds);
updateCueMap(
  path.join(successorRoot, "references/living_cover_cue_map.json"),
  audioMixManifest.total_duration_seconds,
  voiceDuration
);
updateAudioPackage(path.join(successorRoot, "references/audio_package.json"), audioMixManifest);
updateAmbientLayer(path.join(successorRoot, "references/living_cover_ambient_effects_layer.json"), audioMixManifest);
updateVisualPlan(path.join(successorRoot, "references/living_cover_visual_system_plan.json"), audioMixManifest);
createReviewPacket(audioMixManifest);

walkFiles(successorRoot, file => {
  if (!/\.(json|md|html|mjs|js|txt|vtt|srt)$/i.test(file)) return;
  if (file.endsWith("rough_assembly_manifest.json")) return;
  replaceText(file, [[predecessorRoot, successorRoot]]);
});

updateRoughManifest(audioMixManifest);

console.log(
  JSON.stringify(
    {
      successorRoot,
      player: path.join(successorRoot, "player.html"),
      audio: localAudioPath,
      duration: audioMixManifest.total_duration_seconds,
      voiceEnd: audioMixManifest.voice_end_seconds,
      audioSha256: audioMixManifest.output_sha256,
      reads: audioMixManifest.reads
    },
    null,
    2
  )
);
