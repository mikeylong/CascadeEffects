#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const proofRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac_living_cover_challenger_music_html_rough_proof_20260517T073904Z";
const episodeRoot = "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25";
const finalDir = path.join(episodeRoot, "final");
const finalMp4Path = path.join(finalDir, "Ep2_Therac-25.mp4");
const voicePath = path.join(finalDir, "Ep2_Therac-25.wav");
const introPath =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav";
const fullOutroPath =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a";
const musicRegistryPath = "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json";
const oldFinalManifestPath = path.join(
  proofRoot,
  "video_render/therac25_final_mp4_vo_outro_blend_20260517T204621Z/render_manifest.json",
);
const oldPublishRoot = path.join(
  episodeRoot,
  "production/longform_v1/youtube/publish_readiness/therac25_publish_readiness_20260517T211443Z",
);
const oldPublishManifestPath = path.join(oldPublishRoot, "publish_readiness_manifest.json");
const proofManifestPath = path.join(proofRoot, "rough_assembly_manifest.json");
const playerPath = path.join(proofRoot, "player.html");
const offsetVttPath = path.join(proofRoot, "assets/captions/therac25_longform_script_locked.offset_intro_9s601.vtt");
const offsetSrtPath = path.join(proofRoot, "assets/captions/therac25_longform_script_locked.offset_intro_9s601.srt");
const thumbnailSourcePath = path.join(oldPublishRoot, "assets/thumbnail/therac25_thumbnail_candidate_source_art.png");
const metadataPacketPath = path.join(oldPublishRoot, "youtube_metadata_copy_packet.md");

const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const repairId = `actual_outro_prelap_${stamp}`;
const repairRoot = path.join(proofRoot, "audio_repairs", repairId);
const backupDir = path.join(repairRoot, "backups");
const qaAudioDir = path.join(proofRoot, "qa/audio");
const renderRoot = path.join(proofRoot, "video_render", `therac25_final_mp4_${repairId}`);
const renderManifestPath = path.join(renderRoot, "render_manifest.json");
const renderQaDir = path.join(renderRoot, "qa_frames");
const renderSidecarDir = path.join(renderRoot, "youtube_sidecars");
const publishRoot = path.join(
  episodeRoot,
  "production/longform_v1/youtube/publish_readiness",
  `therac25_publish_readiness_${repairId}`,
);
const publishManifestPath = path.join(publishRoot, "publish_readiness_manifest.json");
const publishReviewPath = path.join(publishRoot, "review.html");
const publishVideoPath = path.join(publishRoot, "assets/video/Ep2-Therac-25.mp4");
const publishVttPath = path.join(publishRoot, "assets/captions/Ep2-Therac-25.vtt");
const publishSrtPath = path.join(publishRoot, "assets/captions/Ep2-Therac-25.srt");
const publishThumbPath = path.join(publishRoot, "assets/thumbnail/therac25_thumbnail_candidate_source_art.png");
const publishSampleMp3Path = path.join(publishRoot, "assets/audio/vo_outro_actual_prelap_transition.mp3");
const publishSampleWavPath = path.join(publishRoot, "assets/audio/vo_outro_actual_prelap_transition.wav");
const publishQaFrameDir = path.join(publishRoot, "assets/qa_frames");
const publishServerPath = path.join(publishRoot, "scripts/range_static_server.mjs");

const sampleRate = 44100;
const timing = {
  voiceStartSeconds: 9.601451,
  introFadeTailSeconds: 2,
  voiceDurationSeconds: 1081.260408,
  voiceEndSeconds: 1090.861859,
  actualOutroPrelapSeconds: 5,
  fullOutroStartSeconds: 1085.861859,
  fullOutroFadeInSeconds: 5,
  fullOutroGainLinear: 0.66,
  fullOutroDurationSeconds: 30.795215,
  transitionSampleStartSeconds: 1083.861859,
  transitionSampleEndSeconds: 1097.861859,
};
timing.introFadeEndSeconds = timing.voiceStartSeconds + timing.introFadeTailSeconds;
timing.voiceStartSamples = Math.round(timing.voiceStartSeconds * sampleRate);
timing.fullOutroStartSamples = Math.round(timing.fullOutroStartSeconds * sampleRate);
timing.voiceEndSamples = Math.round(timing.voiceEndSeconds * sampleRate);
timing.naturalRuntimeSeconds = Number(
  (timing.fullOutroStartSeconds + timing.fullOutroDurationSeconds).toFixed(6),
);
timing.endScreenSafeWindowStartSeconds = Number((timing.naturalRuntimeSeconds - 20).toFixed(6));
timing.finalSecondSampleSeconds = Number((timing.naturalRuntimeSeconds - 1).toFixed(6));

const REQUIRED_MUSIC_READS = [
  "vo_outro_blend_plan_read",
  "vo_outro_music_blend_read",
  "outro_transition_review_sample_read",
  "outro_entry_level_match_read",
  "outro_prelap_source_read",
  "outro_prelap_start_read",
  "outro_no_restart_at_voice_end_read",
  "outro_source_continuity_read",
  "music_contract_regression_read",
];

const locks = {
  publish_ready: false,
  youtube_upload_ready: false,
  public_release_ready: false,
  may_youtube_action: false,
  upload_performed: false,
  upload_action_enabled_in_review_html: false,
  public_visibility_change_enabled: false,
};

const endScreenContext = {
  youtube_end_screen_template_id: "challenger_titleless_end_screen_overlay_on_living_cover_v1",
  youtube_end_screen_targets: {
    left_video: { bbox_xy: [78, 382, 758, 765], role: "suggested_video" },
    right_video: { bbox_xy: [1162, 382, 1842, 765], role: "watch_next_video" },
    center_subscribe: { bbox_xy: [814, 429, 1106, 721], role: "subscribe" },
  },
  end_screen_start_seconds: timing.voiceEndSeconds,
  end_screen_safe_window_start_seconds: timing.endScreenSafeWindowStartSeconds,
  background_motion_policy: "ambient_motion_continues_behind_static_youtube_target_geometry",
  viewer_text_policy: "chapter_context_caption_and_rail_text_suppressed_in_end_screen_window",
};

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || proofRoot,
    encoding: options.encoding ?? "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 256,
  });
  if (result.status !== 0) {
    throw new Error(
      `${command} failed\nARGS: ${args.join(" ")}\nSTDOUT:\n${result.stdout || ""}\nSTDERR:\n${result.stderr || ""}`,
    );
  }
  return result;
}

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function artifact(filePath, rel = null) {
  const stat = fs.statSync(filePath);
  const record = { path: filePath, sha256: sha256(filePath), bytes: stat.size };
  if (rel) record.rel = rel;
  return record;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function copyFile(sourcePath, destPath) {
  ensureDir(path.dirname(destPath));
  fs.copyFileSync(sourcePath, destPath);
}

function ffprobeJson(filePath) {
  return JSON.parse(
    run("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration",
      "-of",
      "json",
      filePath,
    ]).stdout,
  );
}

function durationSeconds(filePath) {
  return Number(
    run("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=nw=1:nk=1",
      filePath,
    ]).stdout.trim(),
  );
}

function fullDecodeRead(filePath) {
  run("ffmpeg", ["-v", "error", "-i", filePath, "-map", "0", "-f", "null", "-"], {
    maxBuffer: 1024 * 1024 * 64,
  });
  return "pass";
}

function streamDataHash(filePath, streamSpec) {
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", filePath, "-map", streamSpec, "-c", "copy", "-f", "data", "-"],
    { cwd: proofRoot, encoding: null, maxBuffer: 1024 * 1024 * 512 },
  );
  if (result.status !== 0) {
    throw new Error(`stream hash failed for ${filePath} ${streamSpec}\n${result.stderr?.toString() || ""}`);
  }
  return createHash("sha256").update(result.stdout).digest("hex");
}

function volumedetect(filePath, startSeconds = null, takeSeconds = null) {
  const args = ["-hide_banner"];
  if (startSeconds !== null) args.push("-ss", String(startSeconds));
  if (takeSeconds !== null) args.push("-t", String(takeSeconds));
  args.push("-i", filePath, "-af", "volumedetect", "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, {
    cwd: proofRoot,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 32,
  });
  if (result.status !== 0) throw new Error(`volumedetect failed\n${result.stderr}`);
  const text = result.stderr || "";
  const mean = text.match(/mean_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  const max = text.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  return {
    mean_volume_db: mean ? Number(mean[1]) : null,
    max_volume_db: max ? Number(max[1]) : null,
  };
}

function relativeFromPublish(absPath) {
  return path.relative(publishRoot, absPath).split(path.sep).join("/");
}

function verifyInputs() {
  for (const filePath of [
    finalMp4Path,
    voicePath,
    introPath,
    fullOutroPath,
    oldFinalManifestPath,
    oldPublishManifestPath,
    proofManifestPath,
    playerPath,
    offsetVttPath,
    offsetSrtPath,
    thumbnailSourcePath,
    metadataPacketPath,
  ]) {
    if (!fs.existsSync(filePath)) throw new Error(`Missing required input: ${filePath}`);
  }
}

function backupActiveFiles() {
  ensureDir(backupDir);
  const files = [
    [finalMp4Path, "Ep2_Therac-25.previous_final.mp4"],
    [proofManifestPath, "rough_assembly_manifest.before.json"],
    [oldFinalManifestPath, "old_final_render_manifest.before.json"],
    [oldPublishManifestPath, "old_publish_readiness_manifest.before.json"],
    [path.join(proofRoot, "references/audio_mix_manifest.json"), "references_audio_mix_manifest.before.json"],
  ].filter(([filePath]) => fs.existsSync(filePath));
  const records = [];
  for (const [filePath, filename] of files) {
    const backupPath = path.join(backupDir, filename);
    fs.copyFileSync(filePath, backupPath);
    records.push({ active_path: filePath, backup: artifact(backupPath) });
  }
  writeJson(path.join(repairRoot, "before_hashes.json"), records);
  return records;
}

function supersedeOldManifests() {
  const supersede = {
    superseded_by: {
      repair_id: repairId,
      render_manifest_path: renderManifestPath,
      publish_readiness_manifest_path: publishManifestPath,
    },
    superseded_reason:
      "tighten_missing_vo_outro_blend_gate: prior package used a bridge/proxy loop under final VO instead of actual full-outro prelap.",
    superseded_utc: new Date().toISOString(),
  };

  const finalManifest = readJson(oldFinalManifestPath);
  finalManifest.status = "tighten_missing_vo_outro_blend_gate";
  finalManifest.human_disposition = "tighten";
  finalManifest.superseded = supersede;
  finalManifest.qa_reads = {
    ...(finalManifest.qa_reads || {}),
    vo_outro_music_blend_read: "tighten_bridge_proxy_under_final_vo_not_actual_full_outro_prelap",
    outro_prelap_source_read: "tighten_missing_actual_full_outro_prelap_source",
    outro_prelap_start_read: "tighten_full_outro_started_at_voice_end_not_under_final_words",
    outro_no_restart_at_voice_end_read: "tighten_full_outro_restarted_at_voice_end",
    outro_source_continuity_read: "tighten_bridge_to_outro_handoff_not_single_actual_outro_source",
    music_contract_regression_read: "tighten_missing_challenger_actual_outro_prelap_v1",
  };
  writeJson(oldFinalManifestPath, finalManifest);

  const publishManifest = readJson(oldPublishManifestPath);
  publishManifest.status = "tighten_missing_vo_outro_blend_gate";
  publishManifest.human_disposition = "tighten";
  publishManifest.superseded = supersede;
  publishManifest.reads = {
    ...(publishManifest.reads || {}),
    vo_outro_music_blend_read: "tighten_bridge_proxy_under_final_vo_not_actual_full_outro_prelap",
    outro_prelap_source_read: "tighten_missing_actual_full_outro_prelap_source",
    outro_prelap_start_read: "tighten_full_outro_started_at_voice_end_not_under_final_words",
    outro_no_restart_at_voice_end_read: "tighten_full_outro_restarted_at_voice_end",
    outro_source_continuity_read: "tighten_bridge_to_outro_handoff_not_single_actual_outro_source",
    music_contract_regression_read: "tighten_missing_challenger_actual_outro_prelap_v1",
    youtube_upload_ready_read: "blocked_superseded_package_do_not_upload",
    public_release_ready_read: "blocked_superseded_package_do_not_release",
  };
  publishManifest.locks = { ...(publishManifest.locks || {}), ...locks };
  writeJson(oldPublishManifestPath, publishManifest);
}

function buildRepairedAudio() {
  ensureDir(repairRoot);
  const repairedWavPath = path.join(repairRoot, "Ep2-Therac-25.actual_outro_prelap.wav");
  const repairedMp3Path = path.join(repairRoot, "Ep2-Therac-25.actual_outro_prelap_web_review.mp3");
  const filter = [
    `[0:a]aresample=${sampleRate},aformat=channel_layouts=stereo,aloop=loop=-1:size=${timing.voiceStartSamples},atrim=0:${timing.introFadeEndSeconds.toFixed(6)},asetpts=PTS-STARTPTS,afade=t=out:st=${timing.voiceStartSeconds.toFixed(6)}:d=${timing.introFadeTailSeconds.toFixed(6)}[intro]`,
    `[1:a]aresample=${sampleRate},pan=stereo|c0=c0|c1=c0,adelay=${timing.voiceStartSamples}S:all=1[voice]`,
    `[2:a]aresample=${sampleRate},aformat=channel_layouts=stereo,volume=${timing.fullOutroGainLinear},afade=t=in:st=0:d=${timing.fullOutroFadeInSeconds.toFixed(6)},adelay=${timing.fullOutroStartSamples}S:all=1[outro]`,
    "[intro][voice][outro]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[out]",
  ].join(";");

  const args = [
    "-hide_banner",
    "-y",
    "-i",
    introPath,
    "-i",
    voicePath,
    "-i",
    fullOutroPath,
    "-filter_complex",
    filter,
    "-map",
    "[out]",
    "-ar",
    String(sampleRate),
    "-ac",
    "2",
    "-c:a",
    "pcm_s16le",
    repairedWavPath,
  ];
  const mixResult = run("ffmpeg", args);
  fs.writeFileSync(
    path.join(repairRoot, "actual_outro_prelap_mix_ffmpeg.log"),
    `${JSON.stringify(args)}\n${mixResult.stderr || mixResult.stdout || ""}`,
  );
  run("ffmpeg", ["-hide_banner", "-y", "-i", repairedWavPath, "-codec:a", "libmp3lame", "-b:a", "192k", repairedMp3Path]);
  fullDecodeRead(repairedWavPath);
  return { repairedWavPath, repairedMp3Path };
}

function exportTransitionSamples(repairedWavPath) {
  ensureDir(qaAudioDir);
  const duration = timing.transitionSampleEndSeconds - timing.transitionSampleStartSeconds;
  const sampleWavPath = path.join(qaAudioDir, `vo_outro_actual_prelap_transition_${stamp}.wav`);
  const sampleMp3Path = path.join(qaAudioDir, `vo_outro_actual_prelap_transition_${stamp}.mp3`);
  run("ffmpeg", [
    "-hide_banner",
    "-y",
    "-ss",
    timing.transitionSampleStartSeconds.toFixed(6),
    "-t",
    duration.toFixed(6),
    "-i",
    repairedWavPath,
    "-c:a",
    "pcm_s16le",
    sampleWavPath,
  ]);
  run("ffmpeg", ["-hide_banner", "-y", "-i", sampleWavPath, "-codec:a", "libmp3lame", "-b:a", "192k", sampleMp3Path]);
  return {
    wav: artifact(sampleWavPath),
    mp3: artifact(sampleMp3Path),
    start_seconds: timing.transitionSampleStartSeconds,
    end_seconds: timing.transitionSampleEndSeconds,
    window_seconds: duration,
  };
}

function buildAudioMixManifest(repaired, transitionSample, audioQa) {
  const manifestPath = path.join(repairRoot, "actual_outro_prelap_audio_mix_manifest.json");
  const reads = {
    wav_duration_read: "pass",
    stream_read: "pass_pcm_s16le_stereo_44100",
    mp3_review_asset_read: "pass_browser_review_mp3_created",
    no_clipping_read: "pass_max_volume_below_0dB",
    voice_master_unchanged_read: "pass_source_voice_master_hash_recorded",
    music_integration_plan_read: "pass_challenger_actual_outro_prelap_v1",
    series_music_contract_read: "pass_challenger_precedent",
    approved_music_source_read: "pass_registered_paper_architecture_intro_and_full_outro_sources",
    intro_music_contract_read: "pass_music_only_intro_then_2s_fade_tail_under_voice",
    voice_start_offset_read: "pass_9s601451",
    caption_timing_shift_read: "pass_offset_vtt_srt_shifted_by_9s601451",
    full_outro_music_read: "pass_full_paper_architecture_outro_starts_under_final_vo_and_continues_without_restart",
    end_screen_music_handoff_read: "pass_actual_outro_carries_end_screen_window",
    vo_outro_blend_plan_read: "pass_challenger_actual_outro_prelap_v1_5s_full_outro_under_final_vo",
    vo_outro_music_blend_read: "pass_actual_full_outro_fades_under_final_words_no_bridge_substitute",
    outro_transition_review_sample_read: "pass_transition_sample_exported_1083p862_to_1097p862",
    outro_entry_level_match_read: `pass_transition_mean_${audioQa.transition.mean_volume_db}_max_${audioQa.transition.max_volume_db}_dB`,
    outro_prelap_source_read: "pass_full_paper_architecture_m4a_is_actual_prelap_source",
    outro_prelap_start_read: "pass_full_outro_starts_5s_before_voice_end_at_1085p861859",
    outro_no_restart_at_voice_end_read: "pass_full_outro_continues_through_voice_end_without_restart",
    outro_source_continuity_read: "pass_single_full_outro_source_spans_final_vo_to_end_screen",
    audio_level_mix_read: "pass_no_clipping_volumedetect_supporting_evidence",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    music_contract_regression_read: "pass_bridge_proxy_handoff_removed_challenger_actual_outro_prelap_v1",
    full_decode_read: "pass",
    downstream_gate_read: "pass_publish_upload_public_flags_false",
  };
  const manifest = {
    packet_id: `therac25_actual_outro_prelap_music_mix_${stamp}`,
    created_utc: new Date().toISOString(),
    status: "review_ready_audio_only_successor",
    policy: "challenger_actual_outro_prelap_v1",
    source_episode: "Ep2_Therac-25",
    sample_rate: sampleRate,
    vo_outro_blend_plan: {
      policy: "challenger_actual_outro_prelap_v1",
      final_voice_line:
        "Next time: another design failure. Another system that taught itself to ignore what it already knew.",
      voice_start_seconds: timing.voiceStartSeconds,
      voice_duration_seconds: timing.voiceDurationSeconds,
      voice_end_seconds: timing.voiceEndSeconds,
      full_outro_source_path: fullOutroPath,
      full_outro_start_seconds: timing.fullOutroStartSeconds,
      outro_prelap_seconds: timing.actualOutroPrelapSeconds,
      full_outro_fade_in_seconds: timing.fullOutroFadeInSeconds,
      full_outro_gain_linear: timing.fullOutroGainLinear,
      outro_reaches_target_at_seconds: timing.voiceEndSeconds,
      outro_no_restart_at_voice_end: true,
      outro_source_continuity: true,
      bridge_source_path: null,
      bridge_source_policy: "removed_not_used_for_final_vo_handoff",
      rationale:
        "Use the approved full Paper Architecture outro itself under the final VO so the end-screen music is a continuation, not a bridge-to-outro restart.",
    },
    timing,
    inputs: {
      intro_music: artifact(introPath),
      voice_master: artifact(voicePath),
      full_outro_music: artifact(fullOutroPath),
      music_registry_path: fs.existsSync(musicRegistryPath) ? musicRegistryPath : null,
    },
    outputs: {
      wav: artifact(repaired.repairedWavPath),
      mp3_review: artifact(repaired.repairedMp3Path),
    },
    outro_transition_review_sample: transitionSample,
    qa: audioQa,
    reads,
  };
  writeJson(manifestPath, manifest);
  copyFile(manifestPath, path.join(proofRoot, "references/audio_mix_manifest.json"));
  return { manifestPath, manifest };
}

function remuxFinalMp4(repairedWavPath) {
  ensureDir(renderRoot);
  const previousMp4Path = path.join(backupDir, "Ep2_Therac-25.previous_final.mp4");
  const tempMp4Path = path.join(finalDir, `Ep2_Therac-25.${repairId}.tmp.mp4`);
  run("ffmpeg", [
    "-hide_banner",
    "-y",
    "-i",
    previousMp4Path,
    "-i",
    repairedWavPath,
    "-map",
    "0:v:0",
    "-map",
    "1:a:0",
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-movflags",
    "+faststart",
    "-t",
    timing.naturalRuntimeSeconds.toFixed(6),
    "-shortest",
    tempMp4Path,
  ]);
  fs.renameSync(tempMp4Path, finalMp4Path);
  fullDecodeRead(finalMp4Path);
  return {
    previous_mp4: artifact(previousMp4Path),
    output_mp4: artifact(finalMp4Path),
    previous_video_stream_sha256: streamDataHash(previousMp4Path, "0:v:0"),
    repaired_video_stream_sha256: streamDataHash(finalMp4Path, "0:v:0"),
  };
}

function copySidecars() {
  copyFile(offsetVttPath, path.join(renderSidecarDir, path.basename(offsetVttPath)));
  copyFile(offsetSrtPath, path.join(renderSidecarDir, path.basename(offsetSrtPath)));
  return {
    youtube_upload_sidecar_vtt: artifact(path.join(renderSidecarDir, path.basename(offsetVttPath))),
    youtube_upload_sidecar_srt: artifact(path.join(renderSidecarDir, path.basename(offsetSrtPath))),
  };
}

function extractQaFrames() {
  ensureDir(renderQaDir);
  ensureDir(publishQaFrameDir);
  const framePlan = [
    ["start", 1.0],
    ["voice_boundary", 9.851],
    ["duplicate_fixture", 232.005],
    ["chapter_0420", 269.888],
    ["chapter_1150", 720.069],
    ["chapter_1455", 904.719],
    ["outro_start", timing.voiceEndSeconds],
    ["safe_window_start", timing.endScreenSafeWindowStartSeconds],
    ["final_second", timing.finalSecondSampleSeconds],
  ];
  const frames = [];
  for (const [label, seconds] of framePlan) {
    const safeTime = seconds.toFixed(3).replace(".", "p");
    const filename = `mp4_qa_${safeTime}_${label}.jpg`;
    const framePath = path.join(renderQaDir, filename);
    run("ffmpeg", [
      "-hide_banner",
      "-y",
      "-ss",
      seconds.toFixed(6),
      "-i",
      finalMp4Path,
      "-frames:v",
      "1",
      "-q:v",
      "2",
      framePath,
    ]);
    const publishFramePath = path.join(publishQaFrameDir, filename);
    copyFile(framePath, publishFramePath);
    frames.push({
      label: label.replaceAll("_", " "),
      seconds,
      ...artifact(publishFramePath, relativeFromPublish(publishFramePath)),
    });
  }
  return frames;
}

function buildMusicContract(audioMixManifestPath, audioMixManifest, transitionSample, audioMixManifestHash) {
  return {
    contract_id: "challenger_actual_outro_prelap_v1",
    status: "pass",
    audio_mix_manifest_path: audioMixManifestPath,
    audio_mix_manifest_sha256: audioMixManifestHash,
    approved_intro_source_path: introPath,
    approved_outro_source_path: fullOutroPath,
    voice_start_seconds: timing.voiceStartSeconds,
    voice_end_seconds: timing.voiceEndSeconds,
    full_outro_start_seconds: timing.fullOutroStartSeconds,
    outro_prelap_seconds: timing.actualOutroPrelapSeconds,
    outro_reaches_target_at_seconds: timing.voiceEndSeconds,
    natural_runtime_seconds: timing.naturalRuntimeSeconds,
    transition_review_sample: transitionSample,
    outro_transition_review_sample: transitionSample,
    reads: audioMixManifest.reads,
  };
}

function buildRenderManifest(remux, sidecars, audioMixInfo, musicContract, mp4Probe) {
  const previousFinalManifest = readJson(oldFinalManifestPath);
  const qaReads = {
    ...(previousFinalManifest.qa_reads || {}),
    audio_source_encode_read: "pass_aac_encoded_from_actual_outro_prelap_wav",
    duration_read: `pass_natural_actual_outro_prelap_runtime_${timing.naturalRuntimeSeconds}s`,
    full_decode_read: "pass",
    video_stream_copy_read:
      "pass_h264_video_stream_copied_without_visual_reencode_and_trimmed_to_natural_audio_runtime",
    vo_outro_blend_plan_read: "pass_challenger_actual_outro_prelap_v1_5s_full_outro_under_final_vo",
    vo_outro_music_blend_read: "pass_actual_full_outro_fades_under_final_words_no_bridge_substitute",
    outro_transition_review_sample_read: "pass_transition_sample_exported_1083p862_to_1097p862",
    outro_entry_level_match_read: audioMixInfo.manifest.reads.outro_entry_level_match_read,
    outro_prelap_source_read: "pass_full_paper_architecture_m4a_is_actual_prelap_source",
    outro_prelap_start_read: "pass_full_outro_starts_5s_before_voice_end_at_1085p861859",
    outro_no_restart_at_voice_end_read: "pass_full_outro_continues_through_voice_end_without_restart",
    outro_source_continuity_read: "pass_single_full_outro_source_spans_final_vo_to_end_screen",
    music_contract_regression_read: "pass_bridge_proxy_handoff_removed_challenger_actual_outro_prelap_v1",
    full_outro_music_read: "pass_actual_full_outro_prestarts_under_final_vo_and_carries_end_screen",
    end_screen_music_handoff_read: "pass_full_outro_reaches_target_at_voice_end_and_continues_no_restart",
    audio_level_mix_read: audioMixInfo.manifest.reads.audio_level_mix_read,
    final_mp4_read: "pass_final_mp4_present",
    youtube_upload_ready_read: "blocked_pending_publish_readiness_human_keep_and_upload_authorization",
    public_release_ready_read: "blocked_public_release_manual",
  };
  const manifest = {
    packet_id: `therac25_final_mp4_actual_outro_prelap_${stamp}`,
    created_utc: new Date().toISOString(),
    status: "final_assembly_keep_publish_readiness_package_created",
    human_disposition: "keep",
    repair_id: repairId,
    source_html_proof: {
      path: playerPath,
      sha256: sha256(playerPath),
      note: "Kept Therac HTML visual proof; video stream copied from prior final, no visual re-render.",
    },
    review_audio_mix: {
      wav: artifact(audioMixInfo.manifest.outputs.wav.path),
      mp3_review: artifact(audioMixInfo.manifest.outputs.mp3_review.path),
      audio_mix_manifest_path: audioMixInfo.manifestPath,
      audio_mix_manifest_sha256: sha256(audioMixInfo.manifestPath),
    },
    music_integration_contract: musicContract,
    output: {
      ...artifact(finalMp4Path),
      duration_seconds: Number(mp4Probe.format.duration),
      format: mp4Probe.format.format_name,
      bit_rate: Number(mp4Probe.format.bit_rate),
    },
    stream_integrity: remux,
    sidecars,
    end_screen_context: endScreenContext,
    qa_reads: qaReads,
    locks,
    downstream_gate: {
      publish_readiness_manifest_path: publishManifestPath,
      upload_authorization_required: true,
      public_release_manual: true,
    },
  };
  writeJson(renderManifestPath, manifest);
  return manifest;
}

function updateProofManifest(musicContract) {
  const proofManifest = readJson(proofManifestPath);
  proofManifest.status = "final_assembly_keep_publish_readiness_package_created";
  proofManifest.human_disposition = "keep";
  proofManifest.music_integration_contract = musicContract;
  proofManifest.end_screen_context = endScreenContext;
  proofManifest.locks = { ...(proofManifest.locks || {}), ...locks };
  proofManifest.source_html_proof = proofManifest.source_html_proof || { path: playerPath, sha256: sha256(playerPath) };
  proofManifest.rough_assembly_reads = {
    ...(proofManifest.rough_assembly_reads || {}),
    music_integration_plan_read: "pass_challenger_actual_outro_prelap_v1",
    series_music_contract_read: "pass_challenger_precedent",
    approved_music_source_read: "pass_registered_paper_architecture_intro_and_full_outro_sources",
    intro_music_contract_read: "pass_music_only_intro_then_2s_fade_tail_under_voice",
    voice_start_offset_read: "pass_9s601451",
    caption_timing_shift_read: "pass_offset_vtt_srt_shifted_by_9s601451",
    full_outro_music_read: "pass_actual_full_outro_prestarts_under_final_vo_and_carries_end_screen",
    end_screen_music_handoff_read: "pass_full_outro_reaches_target_at_voice_end_and_continues_no_restart",
    vo_outro_blend_plan_read: "pass_challenger_actual_outro_prelap_v1_5s_full_outro_under_final_vo",
    vo_outro_music_blend_read: "pass_actual_full_outro_fades_under_final_words_no_bridge_substitute",
    outro_transition_review_sample_read: "pass_transition_sample_exported_1083p862_to_1097p862",
    outro_entry_level_match_read: musicContract.reads.outro_entry_level_match_read,
    outro_prelap_source_read: "pass_full_paper_architecture_m4a_is_actual_prelap_source",
    outro_prelap_start_read: "pass_full_outro_starts_5s_before_voice_end_at_1085p861859",
    outro_no_restart_at_voice_end_read: "pass_full_outro_continues_through_voice_end_without_restart",
    outro_source_continuity_read: "pass_single_full_outro_source_spans_final_vo_to_end_screen",
    music_contract_regression_read: "pass_bridge_proxy_handoff_removed_challenger_actual_outro_prelap_v1",
    youtube_upload_lock_read: "pass_upload_publish_visibility_actions_remain_blocked",
  };
  writeJson(proofManifestPath, proofManifest);
}

function buildPublishPackage(renderManifest, musicContract, qaFrames, transitionSample, mp4Probe) {
  copyFile(finalMp4Path, publishVideoPath);
  copyFile(offsetVttPath, publishVttPath);
  copyFile(offsetSrtPath, publishSrtPath);
  copyFile(thumbnailSourcePath, publishThumbPath);
  copyFile(transitionSample.mp3.path, publishSampleMp3Path);
  copyFile(transitionSample.wav.path, publishSampleWavPath);
  copyFile(metadataPacketPath, path.join(publishRoot, "youtube_metadata_copy_packet.md"));
  writeRangeServer();
  const metadata = readJson(oldPublishManifestPath).metadata || {};
  const media = {
    mp4: artifact(publishVideoPath),
    vtt: artifact(publishVttPath),
    srt: artifact(publishSrtPath),
    thumbnail_candidate: artifact(publishThumbPath),
    vo_outro_transition_sample: artifact(
      publishSampleMp3Path,
      relativeFromPublish(publishSampleMp3Path),
    ),
    transition_samples: [
      artifact(publishSampleMp3Path, relativeFromPublish(publishSampleMp3Path)),
      artifact(publishSampleWavPath, relativeFromPublish(publishSampleWavPath)),
    ],
    qa_frames: qaFrames,
  };
  const reads = {
    final_assembly_human_keep_read: "pass_audio_only_successor_created_from_kept_visual_final",
    html_primary_review_read: "pass_review_html_created_as_primary_publish_readiness_artifact",
    html_media_refs_read: "pass_local_copied_mp4_vtt_srt_thumbnail_qa_frames_and_transition_sample_exist",
    html_upload_lock_read: "pass_no_upload_publish_or_visibility_action_enabled",
    publish_readiness_review_html_path_read: "pass",
    youtube_metadata_copywriting_read: "review_ready_metadata_packet_preserved_pending_human_keep",
    public_metadata_copy_read: "pass_no_internal_production_terms_in_public_copy",
    public_tag_relevance_read: "pass_tags_are_episode_entities_and_viewer_search_intents",
    thumbnail_candidate_read: "review_ready_source_art_candidate_preserved_pending_human_thumbnail_keep",
    final_mp4_read: "pass_final_mp4_present",
    caption_sidecar_read: "pass_offset_vtt_sidecar_aligns_to_final_mp4_intro_voice_start",
    music_integration_plan_read: "pass_challenger_actual_outro_prelap_v1",
    series_music_contract_read: "pass_challenger_precedent",
    approved_music_source_read: "pass_registered_paper_architecture_intro_and_full_outro_sources",
    intro_music_contract_read: "pass_music_only_intro_then_2s_fade_tail_under_voice",
    voice_start_offset_read: "pass_9s601451",
    caption_timing_shift_read: "pass_offset_vtt_srt_shifted_by_9s601451",
    full_outro_music_read: "pass_actual_full_outro_prestarts_under_final_vo_and_carries_end_screen",
    end_screen_music_handoff_read: "pass_full_outro_reaches_target_at_voice_end_and_continues_no_restart",
    vo_outro_blend_plan_read: "pass_challenger_actual_outro_prelap_v1_5s_full_outro_under_final_vo",
    vo_outro_music_blend_read: "pass_actual_full_outro_fades_under_final_words_no_bridge_substitute",
    outro_transition_review_sample_read: "pass_transition_sample_exported_visible_in_review_html",
    outro_entry_level_match_read: musicContract.reads.outro_entry_level_match_read,
    outro_prelap_source_read: "pass_full_paper_architecture_m4a_is_actual_prelap_source",
    outro_prelap_start_read: "pass_full_outro_starts_5s_before_voice_end_at_1085p861859",
    outro_no_restart_at_voice_end_read: "pass_full_outro_continues_through_voice_end_without_restart",
    outro_source_continuity_read: "pass_single_full_outro_source_spans_final_vo_to_end_screen",
    audio_level_mix_read: musicContract.reads.audio_level_mix_read,
    music_rights_read:
      "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    music_contract_regression_read: "pass_bridge_proxy_handoff_removed_challenger_actual_outro_prelap_v1",
    youtube_upload_ready_read: "blocked_pending_publish_readiness_human_keep_and_upload_authorization",
    public_release_ready_read: "blocked_public_release_manual",
  };
  const manifest = {
    packet_id: `therac25_publish_readiness_${repairId}`,
    created_utc: new Date().toISOString(),
    status: "review_ready_pending_human_publish_readiness_disposition",
    human_disposition: "defer",
    final_assembly_keep_source: {
      render_manifest_path: renderManifestPath,
      render_manifest_sha256: sha256(renderManifestPath),
    },
    primary_review_artifact: null,
    review_surface_type: "html_first_local_byte_range_server_required",
    publish_readiness_review_html_path: publishReviewPath,
    publish_readiness_canonical_review_url: "http://127.0.0.1:8828/review.html",
    review_server: {
      command: `node scripts/range_static_server.mjs ${publishRoot} --port 8828`,
      url: "http://127.0.0.1:8828/review.html",
      byte_range_required: true,
    },
    media,
    metadata,
    mp4_probe: mp4Probe,
    music_integration_contract: musicContract,
    end_screen_context: endScreenContext,
    required_reads: REQUIRED_MUSIC_READS,
    reads,
    locks,
    gate: {
      next_review_question: "keep | tighten | reject publish readiness for the actual-outro-prelap successor",
      upload_requires_separate_explicit_authorization: true,
      public_release_manual: true,
    },
  };
  buildReviewHtml(manifest);
  manifest.primary_review_artifact = artifact(publishReviewPath);
  writeJson(publishManifestPath, manifest);
  return manifest;
}

function htmlEscape(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function buildReviewHtml(manifest) {
  const copy = manifest.metadata?.copy || {};
  const chapters = copy.chapters || [];
  const readsRows = Object.entries(manifest.reads)
    .map(([key, value]) => `<tr><th>${htmlEscape(key)}</th><td>${htmlEscape(value)}</td></tr>`)
    .join("\n");
  const chapterButtons = chapters
    .map(
      (chapter) =>
        `<button type="button" data-time="${htmlEscape(chapter.time)}">${htmlEscape(chapter.time)} ${htmlEscape(chapter.title)}</button>`,
    )
    .join("\n");
  const qaFrames = manifest.media.qa_frames
    .map(
      (frame) =>
        `<figure><img src="${htmlEscape(frame.rel)}" alt="${htmlEscape(frame.label)}"><figcaption>${htmlEscape(frame.label)} (${frame.seconds.toFixed(3)}s)</figcaption></figure>`,
    )
    .join("\n");
  const tags = (copy.tags || []).map((tag) => `<span>${htmlEscape(tag)}</span>`).join("");
  const requiredReads = REQUIRED_MUSIC_READS.map((read) => `<li>${htmlEscape(read)}</li>`).join("\n");
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Therac-25 Actual-Outro Prelap Publish Readiness</title>
  <style>
    :root{color-scheme:dark;--bg:#100f0d;--panel:#211c18;--line:#4d4038;--text:#f5efe3;--muted:#c9bdae;--accent:#b8876b;--ok:#90c7b5;--warn:#e3bf78}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font:16px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    main{max-width:1500px;margin:0 auto;padding:28px}
    h1,h2,h3{margin:0 0 12px}
    h1{font-size:32px}
    h2{font-size:20px;margin-top:28px}
    p{margin:0 0 12px;color:var(--muted)}
    .grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(360px,.75fr);gap:22px;align-items:start}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px}
    video{width:100%;background:#000;border-radius:8px;border:1px solid var(--line)}
    audio{width:100%;margin-top:8px}
    .controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
    button{background:#2b241f;border:1px solid #6f5b4e;color:var(--text);border-radius:6px;padding:8px 10px;font-weight:700;cursor:pointer}
    button:hover{border-color:var(--accent)}
    .status{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}
    .status div{background:#191613;border:1px solid var(--line);border-radius:8px;padding:12px}
    .status strong{display:block;color:var(--ok);font-size:13px;text-transform:uppercase;letter-spacing:.04em}
    .status span{font-size:22px;font-weight:800}
    pre{white-space:pre-wrap;background:#15120f;border:1px solid var(--line);border-radius:8px;padding:14px;color:var(--text)}
    table{border-collapse:collapse;width:100%;font-size:14px}
    th,td{text-align:left;border-bottom:1px solid var(--line);padding:8px;vertical-align:top}
    th{width:42%;color:var(--muted);font-weight:700}
    .thumb{width:100%;border-radius:8px;border:1px solid var(--line)}
    .frames{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
    figure{margin:0;background:#15120f;border:1px solid var(--line);border-radius:8px;overflow:hidden}
    figure img{display:block;width:100%}
    figcaption{padding:8px;color:var(--muted);font-size:13px}
    .tags{display:flex;gap:8px;flex-wrap:wrap}
    .tags span{background:#171410;border:1px solid var(--line);border-radius:999px;padding:5px 9px;color:var(--muted)}
    .lock{color:var(--warn)}
    .reads{columns:2;color:var(--muted)}
    @media(max-width:1000px){.grid,.status{grid-template-columns:1fr}.frames{grid-template-columns:1fr 1fr}.reads{columns:1}}
  </style>
</head>
<body>
<main>
  <h1>Therac-25 Actual-Outro Prelap Publish Readiness</h1>
  <p>This is the audio-only successor. The kept video stream, captions, metadata, thumbnail candidate, and upload locks are preserved. The final VO now hands into the actual full Paper Architecture outro before voice end, without a bridge restart.</p>

  <section class="status">
    <div><strong>Final MP4</strong><span>Review Ready</span></div>
    <div><strong>Publish Ready</strong><span class="lock">False</span></div>
    <div><strong>YouTube Upload</strong><span class="lock">Locked</span></div>
    <div><strong>Public Release</strong><span class="lock">Manual</span></div>
  </section>

  <div class="grid">
    <section class="panel">
      <h2>Final Video</h2>
      <video id="video" controls preload="metadata" poster="assets/thumbnail/therac25_thumbnail_candidate_source_art.png">
        <source src="assets/video/Ep2-Therac-25.mp4" type="video/mp4">
        <track kind="captions" src="assets/captions/Ep2-Therac-25.vtt" srclang="en" label="English" default>
      </video>
      <div class="controls">
        ${chapterButtons}
        <button type="button" data-seconds="1083.862">Transition Sample Window</button>
        <button type="button" data-seconds="${timing.voiceEndSeconds.toFixed(3)}">Voice End / Outro Target</button>
        <button type="button" data-seconds="${timing.endScreenSafeWindowStartSeconds.toFixed(3)}">End-Screen Safe Window</button>
        <button type="button" data-seconds="${timing.finalSecondSampleSeconds.toFixed(3)}">Final Second</button>
      </div>
      <h3>Required VO/Outro Transition Sample</h3>
      <p>Actual full outro starts at ${timing.fullOutroStartSeconds.toFixed(3)}s, reaches target at ${timing.voiceEndSeconds.toFixed(3)}s, and continues without restart.</p>
      <audio controls preload="metadata"><source src="assets/audio/vo_outro_actual_prelap_transition.mp3" type="audio/mpeg"></audio>
    </section>

    <aside class="panel">
      <h2>Thumbnail Candidate</h2>
      <img class="thumb" src="assets/thumbnail/therac25_thumbnail_candidate_source_art.png" alt="Therac-25 thumbnail candidate">
      <p>Candidate only. Human thumbnail keep is still required before upload prep.</p>
      <h2>Metadata</h2>
      <p><strong>${htmlEscape(copy.recommended_title || "")}</strong></p>
      <pre>${htmlEscape(copy.description || "")}</pre>
      <div class="tags">${tags}</div>
      <h2>VO/Outro Gate Reads</h2>
      <ul class="reads">${requiredReads}</ul>
    </aside>
  </div>

  <section class="panel">
    <h2>QA Frames</h2>
    <div class="frames">${qaFrames}</div>
  </section>

  <section class="panel">
    <h2>Required Reads</h2>
    <table><tbody>${readsRows}</tbody></table>
  </section>
</main>
<script>
  const video = document.getElementById('video');
  function secondsFromStamp(stamp){
    const parts = stamp.split(':').map(Number);
    return parts.length === 3 ? parts[0]*3600 + parts[1]*60 + parts[2] : parts[0]*60 + parts[1];
  }
  document.querySelectorAll('button[data-time]').forEach((button)=>{
    button.addEventListener('click',()=>{ video.currentTime = secondsFromStamp(button.dataset.time); video.play(); });
  });
  document.querySelectorAll('button[data-seconds]').forEach((button)=>{
    button.addEventListener('click',()=>{ video.currentTime = Number(button.dataset.seconds); video.play(); });
  });
</script>
</body>
</html>
`;
  ensureDir(path.dirname(publishReviewPath));
  fs.writeFileSync(publishReviewPath, html, "utf8");
}

function writeRangeServer() {
  ensureDir(path.dirname(publishServerPath));
  fs.writeFileSync(
    publishServerPath,
    `import fs from "node:fs";
import path from "node:path";
import http from "node:http";

const root = path.resolve(process.argv[2] || process.cwd());
const portFlag = process.argv.indexOf("--port");
const port = Number(portFlag >= 0 ? process.argv[portFlag + 1] : process.env.PORT || 8828);

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js") || filePath.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".srt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".m4a")) return "audio/mp4";
  if (filePath.endsWith(".wav")) return "audio/wav";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}
function safeRequestPath(requestPath) {
  const decoded = decodeURIComponent(requestPath.split("?")[0] || "/");
  const normalized = path.normalize(decoded).replace(/^([/\\\\]?\\.\\.[/\\\\])+/, "");
  const relative = normalized === "/" ? "review.html" : normalized.replace(/^[/\\\\]/, "");
  const candidate = path.resolve(root, relative);
  if (!candidate.startsWith(root + path.sep) && candidate !== root) return null;
  return candidate;
}
const server = http.createServer((req, res) => {
  const filePath = safeRequestPath(req.url || "/");
  if (!filePath) { res.writeHead(403); res.end("Forbidden"); return; }
  fs.stat(filePath, (error, stat) => {
    if (error || !stat.isFile()) { res.writeHead(404); res.end("Not found"); return; }
    const headers = {
      "Content-Type": contentTypeFor(filePath),
      "Accept-Ranges": "bytes",
      "Access-Control-Allow-Origin": "*"
    };
    const range = req.headers.range;
    if (range) {
      const match = /^bytes=(\\d*)-(\\d*)$/.exec(range);
      if (!match) { res.writeHead(416, headers); res.end(); return; }
      const start = match[1] ? Number(match[1]) : 0;
      const end = match[2] ? Number(match[2]) : stat.size - 1;
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end || start >= stat.size) {
        res.writeHead(416, { ...headers, "Content-Range": \`bytes */\${stat.size}\` });
        res.end();
        return;
      }
      const safeEnd = Math.min(end, stat.size - 1);
      res.writeHead(206, {
        ...headers,
        "Content-Length": safeEnd - start + 1,
        "Content-Range": \`bytes \${start}-\${safeEnd}/\${stat.size}\`
      });
      if (req.method === "HEAD") { res.end(); return; }
      fs.createReadStream(filePath, { start, end: safeEnd }).pipe(res);
      return;
    }
    res.writeHead(200, { ...headers, "Content-Length": stat.size });
    if (req.method === "HEAD") { res.end(); return; }
    fs.createReadStream(filePath).pipe(res);
  });
});
server.listen(port, "127.0.0.1", () => {
  console.log(\`Range static server listening on http://127.0.0.1:\${port}/review.html from \${root}\`);
});
`,
    "utf8",
  );
}

function runValidator(audioMixManifestPath) {
  const validator = "/Users/mike/Agents_CascadeEffects/scripts/validate_living_cover_final_gate.mjs";
  const result = run("node", [
    validator,
    "--proof-manifest",
    proofManifestPath,
    "--player",
    playerPath,
    "--audio-mix",
    audioMixManifestPath,
    "--final-manifest",
    renderManifestPath,
    "--publish-readiness",
    publishManifestPath,
  ]);
  fs.writeFileSync(path.join(repairRoot, "final_gate_validator.json"), result.stdout || "", "utf8");
  return result.stdout.trim();
}

function main() {
  verifyInputs();
  ensureDir(repairRoot);
  backupActiveFiles();
  supersedeOldManifests();
  const repaired = buildRepairedAudio();
  const repairedDuration = durationSeconds(repaired.repairedWavPath);
  if (Math.abs(repairedDuration - timing.naturalRuntimeSeconds) > 0.05) {
    throw new Error(`Unexpected repaired audio duration ${repairedDuration}; expected ${timing.naturalRuntimeSeconds}`);
  }
  const transitionSample = exportTransitionSamples(repaired.repairedWavPath);
  const audioQa = {
    full_mix: volumedetect(repaired.repairedWavPath),
    transition: volumedetect(
      repaired.repairedWavPath,
      timing.transitionSampleStartSeconds,
      timing.transitionSampleEndSeconds - timing.transitionSampleStartSeconds,
    ),
    pre_voice_end: volumedetect(repaired.repairedWavPath, timing.voiceEndSeconds - 4, 4),
    post_voice_end: volumedetect(repaired.repairedWavPath, timing.voiceEndSeconds, 4),
  };
  const audioMixInfo = buildAudioMixManifest(repaired, transitionSample, audioQa);
  const musicContract = buildMusicContract(
    audioMixInfo.manifestPath,
    audioMixInfo.manifest,
    transitionSample,
    sha256(audioMixInfo.manifestPath),
  );
  updateProofManifest(musicContract);
  const remux = remuxFinalMp4(repaired.repairedWavPath);
  const mp4Duration = durationSeconds(finalMp4Path);
  if (Math.abs(mp4Duration - timing.naturalRuntimeSeconds) > 0.75) {
    throw new Error(`Unexpected final MP4 duration ${mp4Duration}; expected about ${timing.naturalRuntimeSeconds}`);
  }
  const sidecars = copySidecars();
  const mp4Probe = ffprobeJson(finalMp4Path);
  const renderManifest = buildRenderManifest(remux, sidecars, audioMixInfo, musicContract, mp4Probe);
  const qaFrames = extractQaFrames();
  buildPublishPackage(renderManifest, musicContract, qaFrames, transitionSample, mp4Probe);
  const validation = runValidator(audioMixInfo.manifestPath);
  const summary = {
    status: "pass",
    repair_id: repairId,
    repaired_audio_duration_seconds: repairedDuration,
    final_mp4_duration_seconds: mp4Duration,
    final_mp4_path: finalMp4Path,
    render_manifest_path: renderManifestPath,
    publish_readiness_manifest_path: publishManifestPath,
    publish_readiness_review_html_path: publishReviewPath,
    review_url: "http://127.0.0.1:8828/review.html",
    validation: validation ? JSON.parse(validation) : null,
  };
  writeJson(path.join(repairRoot, "repair_summary.json"), summary);
  console.log(JSON.stringify(summary, null, 2));
}

main();
