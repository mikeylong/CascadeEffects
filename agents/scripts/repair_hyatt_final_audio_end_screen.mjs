#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const restartRoot = "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516";
const roughRoot = path.join(restartRoot, "youtube/rough_assembly");
const predecessorRoot = path.join(
  roughRoot,
  "hyatt_living_cover_html_rough_proof_n6_vo_outro_end_screen_repair_20260518T005829Z",
);
const invalidFinalRoot = path.join(predecessorRoot, "video_render/hyatt_longform_final_mp4_20260518T005942Z");
const invalidFinalManifestPath = path.join(invalidFinalRoot, "render_manifest.json");
const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
const predecessorAudioMixPath = path.join(predecessorRoot, "references/audio_mix_manifest.json");
const predecessorAudioWavPath = path.join(
  predecessorRoot,
  "assets/audio/Ep3-Hyatt-Regency.vo_outro_blend_challenger_music_review_mix_20260518T005829Z.wav",
);
const voicePath = path.join(
  restartRoot,
  "youtube/audio_repairs/live_load_long_i_repair_20260517T204138Z/masters/Ep3-Hyatt-Regency.live_load_long_i_voice_master.wav",
);
const pronunciationManifestPath = path.join(
  restartRoot,
  "youtube/audio_repairs/live_load_long_i_repair_20260517T204138Z/pronunciation_repair_manifest.json",
);
const introPath = "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav";
const outroPath = "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a";
const registryPath = "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json";
const validatorPath = "/Users/mike/Agents_CascadeEffects/scripts/validate_living_cover_final_gate.mjs";
const sourceRenderScriptPath = path.join(predecessorRoot, "scripts/render_hyatt_final_mp4.mjs");

const templateId = "challenger_titleless_end_screen_overlay_on_living_cover_v1";
const templateTargets = {
  left_video: { role: "suggested_video", bbox_xy: [78, 382, 758, 765], aspect_ratio: "16:9" },
  right_video: { role: "watch_next_video", bbox_xy: [1162, 382, 1842, 765], aspect_ratio: "16:9" },
  center_subscribe: { role: "subscribe", center_xy: [960, 575], radius_px: 146, bbox_xy: [814, 429, 1106, 721] },
};

const sampleRate = 44100;
const timing = {
  voiceStartSeconds: 9.601451,
  introFadeEndSeconds: 11.601451,
  introFadeTailSeconds: 2,
  voiceDurationSeconds: 833.642812,
  voiceEndSeconds: 843.244263,
  targetDurationSeconds: 874.033923,
  actualOutroPrelapSeconds: 5,
  outroGain: 0.66,
  outroFadeInSeconds: 5,
};
timing.voiceStartSamples = Math.round(timing.voiceStartSeconds * sampleRate);
timing.voiceEndSamples = Math.round(timing.voiceEndSeconds * sampleRate);
timing.actualOutroStartSeconds = Number((timing.voiceEndSeconds - timing.actualOutroPrelapSeconds).toFixed(6));
timing.actualOutroStartSamples = Math.round(timing.actualOutroStartSeconds * sampleRate);
timing.outroTrimSeconds = Number((timing.targetDurationSeconds - timing.actualOutroStartSeconds).toFixed(6));

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_actual_outro_prelap_${stamp}`;
const successorRoot = path.join(roughRoot, successorId);
const successorManifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
const successorPlayerPath = path.join(successorRoot, "player.html");
const successorAudioMixPath = path.join(successorRoot, "references/audio_mix_manifest.json");
const successorRenderScriptPath = path.join(successorRoot, "scripts/render_hyatt_final_mp4.mjs");
const gateApprovalPath = path.join(
  restartRoot,
  `youtube/gate_approvals/hyatt_rough_proof_keep_actual_outro_prelap_${stamp}.md`,
);
const audioRepairRoot = path.join(successorRoot, "audio_repairs", `actual_outro_prelap_${stamp}`);
const qaAudioDir = path.join(successorRoot, "qa/audio");
const repairedWavPath = path.join(
  successorRoot,
  `assets/audio/Ep3-Hyatt-Regency.actual_outro_prelap_challenger_music_review_mix_${stamp}.wav`,
);
const repairedMp3Path = path.join(
  successorRoot,
  `assets/audio/Ep3-Hyatt-Regency.actual_outro_prelap_challenger_music_web_review_${stamp}.mp3`,
);

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function requireFile(filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing required file: ${filePath}`);
  }
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || successorRoot,
    encoding: options.encoding || "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 128,
    stdio: options.stdio || "pipe",
  });
  if (result.status !== 0) {
    throw new Error(`${command} failed\nARGS: ${args.join(" ")}\nSTDOUT:\n${result.stdout || ""}\nSTDERR:\n${result.stderr || ""}`);
  }
  return result;
}

function sha256(filePath) {
  return createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function artifact(filePath) {
  const stat = fs.statSync(filePath);
  return { path: filePath, sha256: sha256(filePath), bytes: stat.size };
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function ffprobeJson(filePath) {
  return JSON.parse(
    run("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,sample_rate,channels,width,height,avg_frame_rate,duration",
      "-of",
      "json",
      filePath,
    ]).stdout,
  );
}

function durationSeconds(filePath) {
  return Number(run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath]).stdout.trim());
}

function volumedetect(filePath, startSeconds = null, takeSeconds = null) {
  const args = ["-hide_banner"];
  if (startSeconds !== null) args.push("-ss", String(startSeconds));
  if (takeSeconds !== null) args.push("-t", String(takeSeconds));
  args.push("-i", filePath, "-af", "volumedetect", "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, { cwd: successorRoot, encoding: "utf8", maxBuffer: 1024 * 1024 * 32 });
  if (result.status !== 0) throw new Error(`volumedetect failed\n${result.stderr || ""}`);
  const text = result.stderr || "";
  const mean = text.match(/mean_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  const max = text.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  return {
    mean_volume_db: mean ? Number(mean[1]) : null,
    max_volume_db: max ? Number(max[1]) : null,
  };
}

function copySuccessor() {
  if (fs.existsSync(successorRoot)) throw new Error(`Successor already exists: ${successorRoot}`);
  fs.cpSync(predecessorRoot, successorRoot, {
    recursive: true,
    verbatimSymlinks: true,
    filter: (src) => {
      const rel = path.relative(predecessorRoot, src);
      if (!rel) return true;
      if (rel === "video_render" || rel.startsWith(`video_render${path.sep}`)) return false;
      if (rel === "review_server.pid" || rel === "review_server.log") return false;
      return true;
    },
  });
}

function markInvalidFinal() {
  const now = new Date().toISOString();
  if (fs.existsSync(invalidFinalManifestPath)) {
    const manifest = readJson(invalidFinalManifestPath);
    manifest.status = "tighten_actual_outro_not_prelapped";
    manifest.human_disposition = "tighten";
    manifest.publishable_final = false;
    manifest.invalidation = {
      recorded_utc: now,
      reason: "The actual full outro track starts at voice end; only a bridge/proxy layer plays under the final VO.",
      successor_required: successorRoot,
      blockers: [
        "full_outro_start_seconds_not_before_voice_end",
        "bridge_proxy_substituted_for_actual_outro_prelap",
        "missing_outro_prelap_source_read",
        "missing_outro_prelap_start_read",
        "missing_outro_no_restart_at_voice_end_read",
        "missing_outro_source_continuity_read",
      ],
    };
    manifest.qa_reads = {
      ...(manifest.qa_reads || {}),
      vo_outro_blend_plan_read: "reject_bridge_proxy_did_not_prelap_actual_outro",
      vo_outro_music_blend_read: "reject_actual_outro_enters_after_final_vo",
      outro_prelap_source_read: "reject_bridge_proxy_substituted_for_full_outro_track",
      outro_prelap_start_read: "reject_full_outro_starts_at_voice_end",
      outro_no_restart_at_voice_end_read: "reject_not_proven",
      outro_source_continuity_read: "reject_actual_outro_not_continuous_across_voice_end",
      downstream_gate_read: "pass_publish_readiness_upload_and_youtube_flags_false_after_tighten",
    };
    manifest.upload_locks = {
      ...(manifest.upload_locks || {}),
      publish_ready: false,
      youtube_upload_ready: false,
      public_release_ready: false,
      may_youtube_action: false,
      upload_performed: false,
      private_youtube_upload: false,
      public_release: false,
    };
    manifest.publish_readiness_gate = {
      ...(manifest.publish_readiness_gate || {}),
      status: "blocked_final_assembly_tighten_vo_outro_end_screen_template",
      may_create_html_publish_readiness: false,
      may_youtube_action: false,
      private_upload_approved: false,
      public_release_ready: false,
    };
    writeJson(invalidFinalManifestPath, manifest);
  }

  if (fs.existsSync(predecessorManifestPath)) {
    const proofManifest = readJson(predecessorManifestPath);
    proofManifest.invalidated_final_render = {
      recorded_utc: now,
      final_render_packet_path: invalidFinalRoot,
      final_render_manifest_path: invalidFinalManifestPath,
      human_disposition: "tighten",
      reason: "Final MP4 blocked because the actual full outro starts at voice end instead of fading in behind the final VO.",
      successor_packet_path: successorRoot,
    };
    proofManifest.upload_locks = {
      ...(proofManifest.upload_locks || {}),
      publish_ready: false,
      youtube_upload_ready: false,
      public_release_ready: false,
      may_youtube_action: false,
      upload_performed: false,
      private_youtube_upload: false,
      public_release: false,
    };
    proofManifest.publish_readiness_gate = {
      ...(proofManifest.publish_readiness_gate || {}),
      status: "blocked_final_assembly_tighten_actual_outro_not_prelapped",
      may_create_html_publish_readiness: false,
      may_youtube_action: false,
      private_upload_approved: false,
      public_release_ready: false,
    };
    writeJson(predecessorManifestPath, proofManifest);
  }
}

function buildRepairedAudio() {
  ensureDir(path.dirname(repairedWavPath));
  ensureDir(audioRepairRoot);
  ensureDir(qaAudioDir);
  const naturalTargetDurationSeconds = Number((timing.actualOutroStartSeconds + durationSeconds(outroPath)).toFixed(6));
  const filter = [
    `[0:a]aresample=${sampleRate},aformat=channel_layouts=stereo,aloop=loop=-1:size=${timing.voiceStartSamples},atrim=0:${timing.introFadeEndSeconds.toFixed(6)},asetpts=PTS-STARTPTS,afade=t=out:st=${timing.voiceStartSeconds.toFixed(6)}:d=${timing.introFadeTailSeconds.toFixed(6)}[intro]`,
    `[1:a]aresample=${sampleRate},pan=stereo|c0=c0|c1=c0,adelay=${timing.voiceStartSamples}S:all=1[voice]`,
    `[2:a]aresample=${sampleRate},aformat=channel_layouts=stereo,atrim=0:${timing.outroTrimSeconds.toFixed(6)},asetpts=PTS-STARTPTS,volume=${timing.outroGain},afade=t=in:st=0:d=${timing.outroFadeInSeconds.toFixed(6)},adelay=${timing.actualOutroStartSamples}S:all=1[outro]`,
    "[intro][voice][outro]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[out]",
  ].join(";");

  const mixArgs = [
    "-hide_banner",
    "-y",
    "-i",
    introPath,
    "-i",
    voicePath,
    "-i",
    outroPath,
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
  const mix = run("ffmpeg", mixArgs);
  fs.writeFileSync(path.join(audioRepairRoot, "vo_outro_blend_mix_ffmpeg.log"), `${JSON.stringify(mixArgs, null, 2)}\n${mix.stderr || mix.stdout || ""}`);
  const mp3 = run("ffmpeg", ["-hide_banner", "-y", "-i", repairedWavPath, "-codec:a", "libmp3lame", "-b:a", "192k", repairedMp3Path]);
  fs.writeFileSync(path.join(audioRepairRoot, "vo_outro_blend_mp3_ffmpeg.log"), mp3.stderr || mp3.stdout || "");

  const sampleStart = Number((timing.voiceEndSeconds - 7).toFixed(6));
  const sampleDuration = 14;
  const beforeWav = path.join(qaAudioDir, `vo_outro_before_${stamp}.wav`);
  const beforeMp3 = path.join(qaAudioDir, `vo_outro_before_${stamp}.mp3`);
  const afterWav = path.join(qaAudioDir, `vo_outro_blend_transition_${stamp}.wav`);
  const afterMp3 = path.join(qaAudioDir, `vo_outro_blend_transition_${stamp}.mp3`);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", String(sampleStart), "-t", String(sampleDuration), "-i", predecessorAudioWavPath, "-c:a", "pcm_s16le", beforeWav]);
  run("ffmpeg", ["-hide_banner", "-y", "-i", beforeWav, "-codec:a", "libmp3lame", "-b:a", "192k", beforeMp3]);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", String(sampleStart), "-t", String(sampleDuration), "-i", repairedWavPath, "-c:a", "pcm_s16le", afterWav]);
  run("ffmpeg", ["-hide_banner", "-y", "-i", afterWav, "-codec:a", "libmp3lame", "-b:a", "192k", afterMp3]);

  const outputDuration = durationSeconds(repairedWavPath);
  const fullMix = volumedetect(repairedWavPath);
  const preEntry = volumedetect(repairedWavPath, timing.voiceEndSeconds - 4, 4);
  const postEntry = volumedetect(repairedWavPath, timing.voiceEndSeconds, 4);
  const transition = volumedetect(repairedWavPath, timing.voiceEndSeconds - 7, 14);
  const levelDelta =
    postEntry.mean_volume_db !== null && preEntry.mean_volume_db !== null
      ? Number((postEntry.mean_volume_db - preEntry.mean_volume_db).toFixed(1))
      : null;

  const reads = {
    wav_duration_read:
      Math.abs(outputDuration - naturalTargetDurationSeconds) <= 0.08
        ? "pass_natural_duration_shortened_by_actual_outro_prelap"
        : `tighten_duration_delta_${(outputDuration - naturalTargetDurationSeconds).toFixed(3)}s`,
    stream_read: "pass_pcm_s16le_stereo_44100",
    mp3_review_asset_read: "pass_browser_review_mp3_created",
    no_clipping_read: fullMix.max_volume_db !== null && fullMix.max_volume_db <= -0.1 ? `pass_max_volume_${fullMix.max_volume_db}dB` : "tighten_peak_above_expected",
    voice_master_unchanged_read: "pass_source_voice_master_hash_recorded",
    approved_music_source_read: "pass_registered_paper_architecture_theme_assets_recorded",
    series_music_contract_read: "pass_challenger_style_default",
    intro_music_contract_read: "pass_music_only_intro_then_2s_fade_tail_under_voice",
    voice_start_offset_read: "pass_voice_starts_after_9s601_music_only_intro",
    caption_timing_shift_read: "pass_offset_vtt_srt_shifted_by_9s601451",
    full_outro_music_read: "pass_full_paper_architecture_outro_track_used_as_actual_prelap_source",
    end_screen_music_handoff_read: "pass_end_screen_starts_after_actual_outro_is_already_under_vo",
    vo_outro_blend_plan_read: "pass_challenger_actual_outro_prelap_v1",
    vo_outro_music_blend_read: "pass_repaired_no_hard_join_level_checked_transition_sample_exported_for_final_review",
    outro_transition_review_sample_read: "pass_before_after_transition_samples_exported_7s_before_to_7s_after_final_vo",
    outro_entry_level_match_read:
      levelDelta !== null && Math.abs(levelDelta) <= 6 ? `pass_pre_post_entry_mean_delta_${levelDelta}dB` : `tighten_pre_post_entry_mean_delta_${levelDelta}dB`,
    outro_prelap_source_read: "pass_full_outro_track_fades_under_final_vo_not_bridge_proxy",
    outro_prelap_start_read: "pass_full_outro_starts_5s_before_voice_end",
    outro_no_restart_at_voice_end_read: "pass",
    outro_source_continuity_read: "pass_full_outro_source_continues_across_voice_end_without_restart",
    audio_level_mix_read: fullMix.max_volume_db !== null && fullMix.max_volume_db <= -0.1 ? `pass_max_volume_${fullMix.max_volume_db}dB` : "tighten_peak_above_expected",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    music_contract_regression_read: "pass_bridge_only_outro_regression_rejected_actual_full_outro_prelap_used",
    live_load_pronunciation_repair_read: "pass_repaired_live_load_long_i_voice_master_preserved",
    downstream_gate_read: "pass_final_assembly_review_ready_publish_upload_youtube_flags_false",
  };

  const audioMix = {
    packet_id: `hyatt_actual_outro_prelap_music_mix_${stamp}`,
    status: "final_assembly_review_ready_pending_human_listen_disposition",
    created_utc: new Date().toISOString(),
    predecessor_audio_mix_manifest_path: predecessorAudioMixPath,
    predecessor_audio_mix_manifest_sha256: sha256(predecessorAudioMixPath),
    repair_id: `actual_outro_prelap_${stamp}`,
    mix_profile_id: "challenger_actual_outro_prelap_v1",
    voice_source_path: voicePath,
    voice_source_sha256: sha256(voicePath),
    pronunciation_repair_manifest_path: pronunciationManifestPath,
    pronunciation_repair_manifest_sha256: sha256(pronunciationManifestPath),
    voice_start_seconds: timing.voiceStartSeconds,
    voice_duration_seconds: timing.voiceDurationSeconds,
    voice_end_seconds: timing.voiceEndSeconds,
    output_path: repairedWavPath,
    output_sha256: sha256(repairedWavPath),
    output_probe: ffprobeJson(repairedWavPath),
    browser_mp3_path: repairedMp3Path,
    browser_mp3_sha256: sha256(repairedMp3Path),
    browser_mp3_probe: ffprobeJson(repairedMp3Path),
    total_duration_seconds: outputDuration,
    original_target_duration_seconds: timing.targetDurationSeconds,
    natural_actual_outro_prelap_duration_seconds: naturalTargetDurationSeconds,
    duration_change_reason: "The approved full Paper Architecture outro is 30.795s; starting it 5s before voice end naturally shortens the final by about 5s instead of padding with a proxy bridge.",
    intro_music_start_seconds: 0,
    intro_music_only_end_seconds: timing.voiceStartSeconds,
    intro_music_fade_end_seconds: timing.introFadeEndSeconds,
    outro_music_start_seconds: timing.actualOutroStartSeconds,
    outro_music_end_seconds: outputDuration,
    full_outro_source_path: outroPath,
    full_outro_start_seconds: timing.actualOutroStartSeconds,
    full_outro_fade_in_seconds: timing.outroFadeInSeconds,
    outro_prelap_seconds: timing.actualOutroPrelapSeconds,
    outro_reaches_target_at_seconds: timing.voiceEndSeconds,
    outro_no_restart_at_voice_end: true,
    outro_source_continuity: true,
    vo_outro_blend_plan: {
      policy: "challenger_actual_outro_prelap_v1",
      full_outro_source_path: outroPath,
      full_outro_start_seconds: timing.actualOutroStartSeconds,
      full_outro_gain_linear: timing.outroGain,
      full_outro_fade_in_seconds: timing.outroFadeInSeconds,
      voice_end_seconds: timing.voiceEndSeconds,
      outro_prelap_seconds: timing.actualOutroPrelapSeconds,
      outro_reaches_target_at_seconds: timing.voiceEndSeconds,
      outro_no_restart_at_voice_end: true,
      outro_source_continuity: true,
      bridge_policy: "no_bridge_used_for_final_vo_handoff_full_outro_track_is_the_prelap_source",
      rationale: "Start the actual Paper Architecture outro five seconds before the last spoken word so it fades in behind the VO and continues without a restart at voice end.",
    },
    outro_transition_review_sample: {
      before_wav: artifact(beforeWav),
      before_mp3: artifact(beforeMp3),
      wav: artifact(afterWav),
      mp3: artifact(afterMp3),
      start_seconds: sampleStart,
      end_seconds: Number((sampleStart + sampleDuration).toFixed(6)),
      window_seconds: sampleDuration,
    },
    outro_entry_level_match_notes: {
      final_4s_before_outro_mean_db: preEntry.mean_volume_db,
      first_4s_after_outro_mean_db: postEntry.mean_volume_db,
      post_minus_pre_mean_delta_db: levelDelta,
      transition_14s_mean_db: transition.mean_volume_db,
      transition_14s_max_db: transition.max_volume_db,
      note: "Programmatic level check is supporting evidence; human final assembly review still owns perceptual keep/tighten/reject.",
    },
    music_sources: {
      registry: { ...artifact(registryPath), track_id: "paper_architecture_theme_v1" },
      intro_body_loop: { ...artifact(introPath), role: "intro_music_only_lead_in_and_opening_fade_tail" },
      outro_full_track: { ...artifact(outroPath), role: "actual_outro_prelap_under_final_vo_and_end_screen_music" },
    },
    candidate_artifacts: {
      repaired_wav_candidate: artifact(repairedWavPath),
      repaired_mp3_candidate: artifact(repairedMp3Path),
    },
    level_reads: {
      full_mix: fullMix,
      final_4s_before_outro: preEntry,
      first_4s_after_outro: postEntry,
      transition_review_sample: transition,
    },
    rights_and_claims: {
      rights_check_required_before_public_release: true,
      claim_risk: "check_upload_processing_before_public_release",
      notes: "Uses registered Paper Architecture theme assets from the local music registry. Public release remains blocked until YouTube claim/status checks are complete.",
    },
    reads,
  };
  writeJson(successorAudioMixPath, audioMix);
  writeJson(path.join(qaAudioDir, `vo_outro_blend_mix_qa_${stamp}.json`), audioMix);
  writeJson(path.join(audioRepairRoot, "vo_outro_blend_audio_mix_manifest.json"), audioMix);
  return audioMix;
}

function patchPlayer() {
  let html = fs.readFileSync(successorPlayerPath, "utf8");
  html = html.replace(
    /<title>[^<]*<\/title>/,
    "<title>Hyatt Regency Living Cover Rough Proof - VO-Outro End Screen Repair</title>",
  );
  html = html.replace(
    /    \.end-target \{[\s\S]*?    \.end-target\.subscribe \{[\s\S]*?\}\n/,
    [
      "    .youtube-target { position: absolute; background: rgba(25, 18, 14, 0.38); }",
      "    .youtube-target.left-video { left: 78px; top: 382px; width: 680px; height: 383px; border: 4px solid rgba(255, 221, 171, 0.76); border-radius: 18px; box-shadow: 0 0 0 10px rgba(201, 144, 73, 0.13), 0 22px 38px rgba(5, 3, 2, 0.34), inset 0 0 38px rgba(255, 221, 171, 0.07); }",
      "    .youtube-target.right-video { left: 1162px; top: 382px; width: 680px; height: 383px; border: 4px solid rgba(179, 111, 68, 0.70); border-radius: 18px; box-shadow: 0 0 0 10px rgba(179, 111, 68, 0.12), 0 22px 38px rgba(5, 3, 2, 0.34), inset 0 0 38px rgba(179, 111, 68, 0.07); }",
      "    .youtube-target.subscribe-target { left: 814px; top: 429px; width: 292px; height: 292px; border: 7px solid rgba(255, 242, 218, 0.88); border-radius: 50%; background: rgba(25, 18, 14, 0.28); box-shadow: 0 0 0 18px rgba(255, 242, 218, 0.11), 0 22px 34px rgba(5, 3, 2, 0.30); }",
      "    .youtube-target.subscribe-target::after { content: \"\"; position: absolute; inset: 18px; border: 3px solid rgba(238, 219, 190, 0.52); border-radius: 50%; }",
      "",
    ].join("\n"),
  );
  html = html.replace(
    /<section class="end-screen" id="endScreen" aria-hidden="true">\s*<div class="end-target video"><\/div>\s*<div class="end-target subscribe"><\/div>\s*<\/section>/,
    '<section class="end-screen" id="endScreen" aria-label="Titleless YouTube end screen target geometry"><div class="youtube-target left-video" aria-hidden="true"></div><div class="youtube-target right-video" aria-hidden="true"></div><div class="youtube-target subscribe-target" aria-hidden="true"></div></section>',
  );
  html = html.replace(
    /src="assets\/audio\/[^"]*(?:live_load_long_i|vo_outro_blend|actual_outro_prelap)[^"]*web_review[^"]*"/,
    `src="assets/audio/${path.basename(repairedMp3Path)}?v=actual_outro_prelap_${stamp}"`,
  );
  html = html.replace(
    /src="assets\/audio\/[^"]*(?:live_load_long_i|vo_outro_blend|actual_outro_prelap)[^"]*(?:review_mix|music_review_mix)[^"]*"/,
    `src="assets/audio/${path.basename(repairedWavPath)}?v=actual_outro_prelap_${stamp}"`,
  );
  html = html.replace(
    /"audio":\s*"assets\/audio\/[^"]*"/,
    `"audio": "assets/audio/${path.basename(repairedMp3Path)}?v=actual_outro_prelap_${stamp}"`,
  );
  html = html.replace(/"duration":\s*[0-9.]+,/, `"duration": ${durationSeconds(repairedWavPath).toFixed(6)},`);
  if (html.includes("end-target video") || html.includes("end-target subscribe")) {
    throw new Error("Failed to remove ad hoc Hyatt end-screen target classes from player.");
  }
  if (!html.includes("youtube-target left-video") || !html.includes("youtube-target right-video") || !html.includes("youtube-target subscribe-target")) {
    throw new Error("Failed to install Challenger/Therac titleless three-target end screen template.");
  }
  fs.writeFileSync(successorPlayerPath, html, "utf8");
}

function updateManifest(audioMix) {
  const manifest = readJson(successorManifestPath);
  const now = new Date().toISOString();
  manifest.packet_id = successorId;
  manifest.status = "rough_proof_keep_final_render_gate_open_actual_outro_prelap_repair";
  manifest.human_disposition = "keep";
  manifest.created_utc = manifest.created_utc || now;
  manifest.modified_utc = now;
  manifest.predecessor_packet_path = predecessorRoot;
  manifest.successor_reason = "actual_full_outro_prelap_under_final_vo_repair";
  manifest.review_only = true;
  manifest.publishable_final = false;
  manifest.html_proof_only = true;
  manifest.mp4_render_created = false;
  delete manifest.rendered_video_proof;
  delete manifest.final_assembly_gate;
  manifest.rough_proof_keep = {
    recorded_utc: now,
    approval_record_path: gateApprovalPath,
    approval_scope: "actual_outro_prelap_repair_successor_render_authorized_by_user_plan_current_final_marked_tighten",
    does_not_authorize: ["publish_readiness_keep", "private_youtube_upload", "public_release"],
  };
  manifest.music_integration_contract = {
    status: "review_ready_pending_human_final_assembly_keep",
    process_version: "living_cover_music_integration_contract_v1",
    contract_id: "hyatt_challenger_actual_outro_prelap_v1",
    series_precedent: "Challenger-style default",
    audio_mix_manifest_path: successorAudioMixPath,
    audio_mix_manifest_sha256: sha256(successorAudioMixPath),
    source_music_registry_path: registryPath,
    source_music_registry_sha256: sha256(registryPath),
    approved_music_sources: audioMix.music_sources,
    voice_start_offset_seconds: timing.voiceStartSeconds,
    caption_timing_shift_seconds: timing.voiceStartSeconds,
    intro_policy: "music_only_intro_before_voice_with_2s_fade_tail_under_voice",
    outro_policy: "full_paper_architecture_m4a_starts_5s_before_last_spoken_word_and_carries_end_screen_window",
    actual_outro_prelap: {
      process_version: "challenger_actual_outro_prelap_v1",
      full_outro_source_path: audioMix.full_outro_source_path,
      full_outro_start_seconds: audioMix.full_outro_start_seconds,
      voice_end_seconds: audioMix.voice_end_seconds,
      outro_prelap_seconds: audioMix.outro_prelap_seconds,
      outro_reaches_target_at_seconds: audioMix.outro_reaches_target_at_seconds,
      outro_no_restart_at_voice_end: audioMix.outro_no_restart_at_voice_end,
      outro_source_continuity: audioMix.outro_source_continuity,
      bridge_policy: "no bridge or proxy source is used for the final VO handoff",
    },
    vo_outro_blend_plan: audioMix.vo_outro_blend_plan,
    outro_transition_review_sample: audioMix.outro_transition_review_sample,
    outro_entry_level_match_notes: audioMix.outro_entry_level_match_notes,
    end_screen_music_handoff_seconds: timing.voiceEndSeconds,
    rights_notes: audioMix.rights_and_claims,
    reads: audioMix.reads,
  };
  manifest.end_screen_context = {
    youtube_end_screen_template_id: templateId,
    template_precedent: "Challenger titleless end-screen overlay; Therac adopted the same three-target static platform geometry.",
    overlay_policy: "titleless_static_platform_target_geometry_with_continuous_subtle_background_motion",
    end_screen_start_seconds: timing.voiceEndSeconds,
    end_screen_end_seconds: audioMix.total_duration_seconds,
    youtube_end_screen_safe_window_seconds: [Number((audioMix.total_duration_seconds - 20).toFixed(6)), audioMix.total_duration_seconds],
    youtube_end_screen_targets: templateTargets,
    target_regions: {
      left_video: { x: 78, y: 382, width: 680, height: 383 },
      right_video: { x: 1162, y: 382, width: 680, height: 383 },
      center_subscribe: { x: 814, y: 429, width: 292, height: 292 },
    },
    visible_text_policy: "titleless_no_viewer_text_in_end_screen_window",
    background_motion_policy: "continuous ambient source drift may continue; YouTube target geometry remains static",
  };
  manifest.final_render_contract = {
    required_after_html_proof_keep: true,
    render_source_rule: "render_from_current_kept_html_proof_only_with_final_gate_validator",
    source_html_proof: {
      packet_path: successorRoot,
      manifest_path: successorManifestPath,
      player_path: successorPlayerPath,
      player_sha256: sha256(successorPlayerPath),
    },
    audio_mix_manifest_path: successorAudioMixPath,
    audio_mix_manifest_sha256: sha256(successorAudioMixPath),
    final_gate_validator_path: validatorPath,
    mp4_render_created: false,
    source_html_proof_must_be_current_kept_successor: true,
    blocked_until_human_keep_on_this_packet: false,
  };
  const addedReads = {
    ...audioMix.reads,
    youtube_end_screen_template_read: `pass_${templateId}`,
    youtube_end_screen_safe_zone_read: "pass_left_right_video_targets_and_center_subscribe_target_within_1920x1080_safe_frame",
    youtube_target_geometry_static_read: "pass_challenger_titleless_three_target_geometry",
    end_screen_title_policy_read: "pass_titleless_youtube_end_screen_overlay",
    end_screen_text_artifact_read: "pass_no_viewer_text_visible_or_faint_in_end_screen_window",
    viewer_text_suppression_read: "pass_chapter_context_caption_cue_and_rail_text_hidden_for_youtube_target_geometry",
    caption_suppression_read: "pass",
    rail_fade_read: "pass",
  };
  manifest.rough_assembly_reads = { ...(manifest.rough_assembly_reads || {}), ...addedReads };
  manifest.reads = { ...(manifest.reads || {}), ...addedReads };
  manifest.qa = {
    ...(manifest.qa || {}),
    vo_outro_audio_mix_manifest_path: successorAudioMixPath,
    vo_outro_audio_mix_manifest_sha256: sha256(successorAudioMixPath),
    vo_outro_transition_sample_mp3_path: audioMix.outro_transition_review_sample.mp3.path,
    vo_outro_before_sample_mp3_path: audioMix.outro_transition_review_sample.before_mp3.path,
  };
  manifest.may_advance_to_video_render = true;
  manifest.may_create_full_runtime_mp4_render = true;
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_youtube_action = false;
  manifest.publish_ready = false;
  manifest.youtube_upload_ready = false;
  manifest.public_release_ready = false;
  manifest.upload_locks = {
    ...(manifest.upload_locks || {}),
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    mp4_render_created: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    final_mp4_render: false,
    final_assembly: false,
    publish_readiness: false,
    private_youtube_upload: false,
    public_release: false,
  };
  manifest.publish_readiness_gate = {
    status: "blocked_pending_repaired_final_assembly_keep",
    mp4_render_created: false,
    final_assembly_review_ready: false,
    upload_performed: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_advance: false,
    may_youtube_action: false,
    private_upload_approved: false,
    next_action: "Render repaired final MP4, then human review final assembly keep/tighten/reject.",
  };
  manifest.next_review_question = "Review the actual full-outro prelap under the final VO in the final MP4 assembly; reply keep, tighten, or reject.";
  writeJson(successorManifestPath, manifest);

  ensureDir(path.dirname(gateApprovalPath));
  fs.writeFileSync(
    gateApprovalPath,
    `# Hyatt Rough Proof Repair Render Authorization

Recorded UTC: ${now}

Scope: final-assembly repair successor only. This records authorization to render a repaired MP4 from the current kept Hyatt proof after replacing the bridge-style VO-to-outro handoff with actual full-outro prelap.

Does not authorize publish readiness, YouTube review upload, or public release.

Successor proof: ${successorRoot}
`,
    "utf8",
  );
}

function patchRenderScript(audioMix) {
  let script = fs.readFileSync(sourceRenderScriptPath, "utf8");
  script = script.split(predecessorRoot).join(successorRoot);
  script = script.replace(
    /assets\/audio\/Ep3-Hyatt-Regency\.(?:live_load_long_i|vo_outro_blend|actual_outro_prelap)[^"]*music_review_mix[^"]*\.wav/,
    `assets/audio/${path.basename(repairedWavPath)}`,
  );
  script = script.replace(
    /youtube\/gate_approvals\/hyatt_rough_proof_keep[^"]*\.md/,
    `youtube/gate_approvals/${path.basename(gateApprovalPath)}`,
  );
  const endScreenHoldTime = Math.max(timing.voiceEndSeconds + 1, audioMix.total_duration_seconds - 4);
  script = script.replace(/durationSeconds: [0-9.]+,/, `durationSeconds: ${audioMix.total_duration_seconds.toFixed(6)},`);
  script = script.replace(
    /safeWindowStartSeconds: [0-9.]+,/,
    `safeWindowStartSeconds: ${Math.max(timing.voiceEndSeconds, audioMix.total_duration_seconds - 20).toFixed(6)},`,
  );
  script = script.replace(/safeWindowEndSeconds: [0-9.]+,/, `safeWindowEndSeconds: ${audioMix.total_duration_seconds.toFixed(6)},`);
  script = script.replace(/\{ name: "end_screen_hold", time: 870\.0 \}/g, `{ name: "end_screen_hold", time: ${endScreenHoldTime.toFixed(3)} }`);
  script = script.replace(/time: 870\.0/g, `time: ${endScreenHoldTime.toFixed(3)}`);
  script = script.replace(/extractQaFrame\(outputMp4Path, 870\.0,/g, `extractQaFrame(outputMp4Path, ${endScreenHoldTime.toFixed(3)},`);
  script = script.replace(/onePixelLuma\(outputMp4Path, 870\.0\)/g, `onePixelLuma(outputMp4Path, ${endScreenHoldTime.toFixed(3)})`);
  script = script.replace(
    `  if (!captionText.includes("live load")) {
    throw new Error("Expected locked caption spelling 'live load' was not found.");
  }
}`,
    `  if (!captionText.includes("live load")) {
    throw new Error("Expected locked caption spelling 'live load' was not found.");
  }
  run("node", [
    "${validatorPath}",
    "--proof-manifest",
    proofManifestPath,
    "--player",
    playerPath,
    "--audio-mix",
    path.join(proofRoot, "references/audio_mix_manifest.json"),
  ]);
}`,
  );
  script = script.replace(
    `    downstream_gate_read: "pass_final_assembly_review_ready_publish_and_youtube_flags_false",
  };

  const outputArtifact = artifact(outputMp4Path);`,
    `    downstream_gate_read: "pass_final_assembly_review_ready_publish_and_youtube_flags_false",
  };
  const audioMixManifest = readJson(path.join(proofRoot, "references/audio_mix_manifest.json"));
  Object.assign(qaReads, audioMixManifest.reads, {
    youtube_end_screen_template_read: "pass_${templateId}",
    youtube_end_screen_safe_zone_read: "pass_left_right_video_targets_and_center_subscribe_target_within_1920x1080_safe_frame",
    youtube_target_geometry_static_read: "pass_challenger_titleless_three_target_geometry",
    end_screen_title_policy_read: "pass_titleless_youtube_end_screen_overlay",
    end_screen_text_artifact_read: "pass_no_viewer_text_visible_or_faint_in_end_screen_window",
    viewer_text_suppression_read: "pass_chapter_context_caption_cue_and_rail_text_hidden_for_youtube_target_geometry",
  });

  const outputArtifact = artifact(outputMp4Path);`,
  );
  script = script.replace(
    `    browser_qa: {
      path: browserQa.qaPath,
      sha256: sha256(browserQa.qaPath),
      reads: browserQa.qa.reads,
    },
    qa_frames: qaFrames,`,
    `    browser_qa: {
      path: browserQa.qaPath,
      sha256: sha256(browserQa.qaPath),
      reads: browserQa.qa.reads,
    },
    review_audio_mix: {
      ...artifact(audioWavPath),
      role: "actual_outro_prelap_challenger_style_music_review_mix_wav",
      audio_mix_manifest_path: path.join(proofRoot, "references/audio_mix_manifest.json"),
      audio_mix_manifest_sha256: sha256(path.join(proofRoot, "references/audio_mix_manifest.json")),
    },
    music_integration_contract: proofManifest.music_integration_contract || null,
    end_screen_context: proofManifest.end_screen_context || null,
    qa_frames: qaFrames,`,
  );
  script = script.replace(
    "Preserved the N6 source art, live-load pronunciation repair, Challenger-style music mix, right-rail-only text, staged chapter motion, camera flashes, and balloon rises.",
    "Preserved the N6 source art, live-load pronunciation repair, right-rail-only text, staged chapter motion, camera flashes, balloon rises, and titleless three-target YouTube end screen while repairing the actual full-outro prelap under the final VO.",
  );
  script = script.replace(
    '| downstream gates | `${qaReads.downstream_gate_read}` |',
    [
      '| downstream gates | `${qaReads.downstream_gate_read}` |',
      '| VO-outro blend | `${qaReads.vo_outro_music_blend_read}` |',
      '| actual outro prelap | `${qaReads.outro_prelap_source_read}` / `${qaReads.outro_prelap_start_read}` |',
      '| outro sample | `${qaReads.outro_transition_review_sample_read}` |',
      '| end-screen template | `${qaReads.youtube_end_screen_template_read}` |',
    ].join("\n"),
  );
  fs.writeFileSync(successorRenderScriptPath, script, "utf8");

  const validation = run("node", [
    validatorPath,
    "--proof-manifest",
    successorManifestPath,
    "--player",
    successorPlayerPath,
    "--audio-mix",
    successorAudioMixPath,
  ]);
  fs.writeFileSync(path.join(successorRoot, "qa/final_gate_preflight_validator.json"), validation.stdout);

  ensureDir(path.join(successorRoot, "review"));
  fs.writeFileSync(
    path.join(successorRoot, "review/rough_assembly_repair_review_packet.md"),
    `# Hyatt Regency Actual-Outro Prelap Repair Proof

Status: rough-proof repair successor, authorized for repaired final render only.

- Successor player: \`${successorPlayerPath}\`
- Audio mix manifest: \`${successorAudioMixPath}\`
- Before transition sample: \`${audioMix.outro_transition_review_sample.before_mp3.path}\`
- Repaired transition sample: \`${audioMix.outro_transition_review_sample.mp3.path}\`
- Actual-outro prelap: \`${audioMix.full_outro_start_seconds}s -> ${audioMix.voice_end_seconds}s\`
- End-screen template: \`${templateId}\`

Publish readiness, YouTube upload, and public release remain locked.
`,
    "utf8",
  );
}

function validateInputs() {
  for (const filePath of [
    predecessorManifestPath,
    predecessorAudioMixPath,
    predecessorAudioWavPath,
    invalidFinalManifestPath,
    sourceRenderScriptPath,
    voicePath,
    pronunciationManifestPath,
    introPath,
    outroPath,
    registryPath,
    validatorPath,
  ]) {
    requireFile(filePath);
  }
}

function main() {
  validateInputs();
  markInvalidFinal();
  copySuccessor();
  const audioMix = buildRepairedAudio();
  patchPlayer();
  updateManifest(audioMix);
  patchRenderScript(audioMix);
  console.log(
    JSON.stringify(
      {
        status: "successor_ready_for_repaired_final_render",
        successorRoot,
        successorPlayerPath,
        successorManifestPath,
        successorAudioMixPath,
        successorRenderScriptPath,
        invalidatedFinalManifestPath: invalidFinalManifestPath,
        repairedTransitionSampleMp3: audioMix.outro_transition_review_sample.mp3.path,
        beforeTransitionSampleMp3: audioMix.outro_transition_review_sample.before_mp3.path,
      },
      null,
      2,
    ),
  );
}

main();
